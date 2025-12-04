import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from api_utils import (
    get_tracks_from_service,
    get_team_assignments_from_service,
    deserialize_tracks,
    deserialize_team_assignments,
    get_homographies_from_service,
    id_to_team_ball_acquisition
)

from utils import read_video, save_video, save_ball_overlay_video, save_ball_heatmap
from ball_acq import BallAcquisitionSensor
from shared import download_to_temp, upload_video
from canvas import PlayerTrackDrawer, BallTrackDrawer, TDOverlay
from mongo_writer import save_ball_possession, save_ball_heatmap_mongo


app = FastAPI()

@app.post("/process")
async def process_video(video_name: str, reference_court: str):
    bucket = "basketball-raw-videos"
    ref_bucket = "basketball-panorama-warp"
    key = f"{video_name}.mp4"
    base_court = "imgs/court.png" # Hardcoded, should be moved to bucket

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
    team_assignments = deserialize_team_assignments(team_assignments_json)

    # 4) Ball possession
    ball_sensor = BallAcquisitionSensor()
    ball_acquisition_list = ball_sensor.detect_ball_possession(player_tracks, ball_tracks)

    ball_team_possessions = id_to_team_ball_acquisition(ball_acquisition_list,
                                                        team_assignments)   

    H = get_homographies_from_service(tmp_video_path, tmp_ref_path)

    # 5) Draw overlays
    player_draw = PlayerTrackDrawer()
    ball_draw   = BallTrackDrawer()
    top_down_overlay = TDOverlay(tmp_ref_path, base_court)

    player_vid_frames = player_draw.draw_annotations(
        vid_frames,
        player_tracks,
        team_assignments,
        ball_acquisition_list,
    )
    output_vid_frames = ball_draw.draw_annotations(player_vid_frames, ball_tracks)

    td_tracks = top_down_overlay.get_td_tracks(player_tracks, team_assignments, H)

    output_vid_frames = top_down_overlay.draw_overlay(
        output_vid_frames,
        td_tracks
    )

    # 6) Create Ball Heatmap Video and Figure
    for i, b in enumerate(ball_tracks[:5]):
        print(f"BALL TRACK[{i}] = {b}")

    td_ball = top_down_overlay.get_ball_td_track(ball_tracks, H)
    ball_frames, heatmap = top_down_overlay.draw_ball_overlay(td_ball)

    save_ball_overlay_video(ball_frames, video_name)
    save_ball_heatmap(heatmap, video_name)
    save_ball_heatmap_mongo(video_name, heatmap)

    # 7) Save & upload
    out_path = f"output_videos/{video_name}.mp4"
    save_video(output_vid_frames, out_path)

    # 8) HTML req. proper .mp4 packaging, fix with ffmpeg
    fixed_path = f"output_videos/{video_name}_fixed.mp4"
    os.system(
        f"ffmpeg -y -i {out_path} -vcodec libx264 -preset fast -movflags +faststart {fixed_path}"
    )

    # 9) upload vid to bucket
    upload_video(local_path=fixed_path, key=key, BUCKET_NAME="basketball-processed")

    # 10) upload ball possession statistics to mongodb
    save_ball_possession(video_name, ball_team_possessions)

    return JSONResponse({
        "status": "completed",
        "ball_tp": f"{ball_team_possessions}",
        "vid_name": f"{video_name}"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)