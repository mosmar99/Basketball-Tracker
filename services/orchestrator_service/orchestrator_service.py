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
)

from shared import download_to_temp, upload_video
from utils import read_video, save_video
from canvas import PlayerTrackDrawer, BallTrackDrawer, TDOverlay
from ball_acq import BallAcquisitionSensor

app = FastAPI()

@app.post("/process")
async def process_video(video_name: str):
    bucket = "basketball-raw-videos"
    key = f"{video_name}.mp4"
    court_reference = "imgs/full_court_warped.jpg" # Hardcoded, should be moved to bucket
    base_court = "imgs/court.png" # Hardcoded, should be moved to bucket

    # 1) Download raw video
    tmp_video_path = download_to_temp(key=key, bucket=bucket)
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

    H = get_homographies_from_service(tmp_video_path, court_reference)

    # 5) Draw overlays
    player_draw = PlayerTrackDrawer()
    ball_draw   = BallTrackDrawer()
    top_down_overlay = TDOverlay(court_reference, base_court)

    player_vid_frames = player_draw.draw_annotations(
        vid_frames,
        player_tracks,
        team_assignments,
        ball_acquisition_list,
    )
    output_vid_frames = ball_draw.draw_annotations(player_vid_frames, ball_tracks)

    output_vid_frames = top_down_overlay.draw_overlay(
        output_vid_frames,
        player_tracks,
        team_assignments,
        H,
    )

    # 6) Save & upload
    out_path = f"output_videos/{video_name}.mp4"
    save_video(output_vid_frames, out_path)

    fixed_path = f"output_videos/{video_name}_fixed.mp4"
    os.system(
        f"ffmpeg -y -i {out_path} -vcodec libx264 -preset fast -movflags +faststart {fixed_path}"
    )

    upload_video(local_path=fixed_path, key=key, BUCKET_NAME="basketball-processed")

    return JSONResponse({
        "status": "completed",
        "output_video": f"{key}"
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)