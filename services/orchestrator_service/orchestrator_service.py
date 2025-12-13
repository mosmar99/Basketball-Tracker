import os
import json
import uvicorn
import numpy as np
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from orchestrator_service.api_utils import (
    get_tracks_from_service,
    get_team_assignments_from_service,
    deserialize_tracks,
    deserialize_team_assignments,
    get_homographies_from_service,
    id_to_team_ball_acquisition,
)

from orchestrator_service.mongo_writer import (
    save_ball_possession,
    save_control_stats,
)

from shared import download_to_temp, upload_video
from shared.utils import read_video, save_video
from orchestrator_service.canvas import PlayerTrackDrawer, BallTrackDrawer, TDOverlay
from orchestrator_service.ball_acq import BallAcquisitionSensor

app = FastAPI()
Instrumentator().instrument(app).expose(app)

@app.post("/process")
async def process_video(video_name: str, reference_court: str):
    bucket = "basketball-raw-videos"
    ref_bucket = "basketball-panorama-warp"
    key = f"{video_name}.mp4"
    base_path = os.path.dirname(__file__)
    base_court = os.path.join(base_path, "imgs", "court.jpg")

    # 1) Download raw video
    tmp_video_path = download_to_temp(key=key, bucket=bucket)
    tmp_ref_path = download_to_temp(key=reference_court, bucket=ref_bucket)
    vid_frames = read_video(tmp_video_path)

    # 2) Get tracks
    player_tracks_json, ball_tracks_json = get_tracks_from_service(tmp_video_path)
    player_tracks  = deserialize_tracks(player_tracks_json)
    ball_tracks    = deserialize_tracks(ball_tracks_json)

    # 3) Get team assignments
    team_assignments_json = get_team_assignments_from_service(tmp_video_path, player_tracks)
    team_assignments = deserialize_team_assignments(team_assignments_json["team_assignments"])
    team_colors = team_assignments_json["team_colors"]
    print("team colors:: ", team_colors)
    print("col 1:", team_colors["1"])
    # 4) Ball possession
    ball_sensor = BallAcquisitionSensor()
    ball_acquisition_list = ball_sensor.detect_ball_possession(player_tracks, ball_tracks)

    # 4.1) Passes and interceptions per team
    passes_and_interceptions = ball_sensor.get_ball_possession_statistics(team_assignments, ball_tracks)

    ball_team_possessions = id_to_team_ball_acquisition(ball_acquisition_list,
                                                        team_assignments)   

    H = get_homographies_from_service(tmp_video_path, tmp_ref_path)

    # 5) Draw overlays
    player_draw = PlayerTrackDrawer(team_1_color=team_colors["1"], team_2_color=team_colors["2"])
    ball_draw   = BallTrackDrawer()

    player_vid_frames = player_draw.draw_annotations(
        vid_frames,
        player_tracks,
        team_assignments,
        ball_acquisition_list,
    )
    output_vid_frames = ball_draw.draw_annotations(player_vid_frames, ball_tracks)

    top_down_overlay = TDOverlay(tmp_ref_path, base_court, t1_color=team_colors["1"], t2_color=team_colors["2"], xz=1280, yz=720)
    td_tracks = top_down_overlay.get_td_tracks(player_tracks, team_assignments, H)
    minimap_frames = [np.zeros((720, 1280, 3), dtype=np.uint8) for _ in output_vid_frames]

    output_vid_minimap, control_stats = top_down_overlay.draw_overlay(
        minimap_frames,
        td_tracks
    )

    # 6) Save & upload
    out_path = f"output_videos/{video_name}.mp4"
    save_video(output_vid_frames, out_path)

    minimap_out_path = f"output_videos/{video_name}_minimap.mp4"
    save_video(output_vid_minimap, minimap_out_path)

    # 7) HTML req. proper .mp4 packaging, fix with ffmpeg
    fixed_path = f"output_videos/{video_name}_fixed.mp4"
    os.system(
        f"ffmpeg -y -i {out_path} -vcodec libx264 -preset fast -movflags +faststart {fixed_path}"
    )

    minimap_fixed_path = f"output_videos/{video_name}_minimap_fixed.mp4"
    os.system(
        f"ffmpeg -y -i {minimap_out_path} -vcodec libx264 -preset fast -movflags +faststart {minimap_fixed_path}"
    )

    # 8) upload vid to bucket
    upload_video(local_path=fixed_path, key=key, BUCKET_NAME="basketball-processed")
    upload_video(local_path=minimap_fixed_path, key=key, BUCKET_NAME="basketball-minimap")

    # 9) upload ball possession statistics to mongodb
    save_ball_possession(video_name, ball_team_possessions)
    save_control_stats(video_name, control_stats)

    return JSONResponse({
        "status": "completed",
        "ball_tp": f"{ball_team_possessions}",
        "vid_name": f"{video_name}",
        "control_stats": json.dumps(control_stats),
        "pi_stats": json.dumps(passes_and_interceptions),
        "team_colors": json.dumps(team_colors)
    })

@app.get("/ping")
def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)