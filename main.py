from utils import read_video, save_video
from tracking import PlayerTracker, BallTracker, get_player_production_model_path
from canvas import PlayerTrackDrawer, BallTrackDrawer, BallPossessionDrawer, TDOverlay
from team_assigner import TeamAssigner
from ball_acq import BallAcquisitionSensor
from shared import download_to_temp, upload_video
import requests
import json
import os

def get_team_assignments_from_service(local_video_path: str, player_tracks):
    url = "http://localhost:8001/assign_teams"
    tracks_json_str = json.dumps(player_tracks)
    with open(local_video_path, "rb") as f:
        files = {
            "file": (local_video_path, f, "video/mp4"),
            "player_tracks_file": ("player_tracks.json", tracks_json_str.encode("utf-8"), "application/json")
        }
        r = requests.post(url, files=files)
    r.raise_for_status()
    data = r.json()
    return data["team_assignments"]

def get_tracks_from_service(local_video_path: str):
    url = "http://localhost:8000/track"
    with open(local_video_path, "rb") as f:
        files = {"file": (local_video_path, f, "video/mp4")}
        r = requests.post(url, files=files)
    r.raise_for_status()
    data = r.json()
    return data["player_tracks"], data["ball_tracks"]

def get_homographies_from_service(local_video_path: str, local_reference_path: str):
    # Ensure the files exist before trying to open them
    if not os.path.exists(local_video_path):
        raise FileNotFoundError(f"Video file not found: {local_video_path}")
    if not os.path.exists(local_reference_path):
        raise FileNotFoundError(f"Reference image not found: {local_reference_path}")

    url = "http://localhost:8002/homographyvideo"
    
    # Open both files with their own handles
    with open(local_video_path, "rb") as video_file, \
         open(local_reference_path, "rb") as reference_file:
        
        # Use the correct file handles for each part
        files = {
            "video": ("video.mp4", video_file, "video/mp4"),
            "reference": ("reference.jpg", reference_file, "image/jpeg")
        }
        
        print("Sending request to server...")
        r = requests.post(url, files=files)
    
    r.raise_for_status()
    data = r.json()
    
    return data["H"]

def deserialize_tracks(serialized):
    tracks = []
    for frame in serialized:
        frame_dict = {}
        for obj in frame:
            track_id = int(obj["track_id"])
            bbox = obj.get("bbox", [])
            frame_dict[track_id] = {"bbox": bbox}
        tracks.append(frame_dict)
    return tracks

def deserialize_team_assignments(serialized):
    out = []
    for frame in serialized:
        frame_dict = {}
        for entry in frame:
            pid = int(entry["player_id"])
            tid = int(entry["team_id"])
            frame_dict[pid] = tid
        out.append(frame_dict)
    return out

def main():
    # 1) Identify video in MinIO
    vid_name = "video_1"
    bucket = "basketball-raw-videos"              
    key = f"{vid_name}.mp4"
    court_reference = "court_homography_exploration/imgs/full_court_warped.jpg"
    base_court = "court_homography_exploration/imgs/court.png"

    # 2) Download from MinIO to a temp file
    tmp_video_path = download_to_temp(key=key, bucket=bucket)

    # 3) Read frames from that temp file
    vid_frames = read_video(tmp_video_path)

    # 4) Get player and ball tracks from tracks service
    player_tracks_json, ball_tracks_json = get_tracks_from_service(tmp_video_path)
    player_tracks = deserialize_tracks(player_tracks_json)
    ball_tracks = deserialize_tracks(ball_tracks_json)

    # 5) Get player team assignments from assignment service
    team_player_assignments = get_team_assignments_from_service(
        tmp_video_path,
        player_tracks,
    )
    team_player_assignments = deserialize_team_assignments(team_player_assignments)

    # 6) Ball acquisition + ball track cleanup
    ball_acquisition_sensor = BallAcquisitionSensor()
    ball_acquisition_list = ball_acquisition_sensor.detect_ball_possession(
        player_tracks, ball_tracks
    )

    # 7) Get homographies from frames
    H = get_homographies_from_service(tmp_video_path, court_reference)

    # 8) Draw overlays
    player_tracks_drawer = PlayerTrackDrawer()
    ball_track_drawer = BallTrackDrawer()
    ball_possession_drawer = BallPossessionDrawer()
    top_down_overlay = TDOverlay(court_reference, base_court)

    player_vid_frames = player_tracks_drawer.draw_annotations(
        vid_frames,
        player_tracks,
        team_player_assignments,
        ball_acquisition_list,
    )

    output_vid_frames = ball_track_drawer.draw_annotations(
        player_vid_frames,
        ball_tracks,
    )

    output_vid_frames = ball_possession_drawer.draw_ball_possession(
        output_vid_frames,
        team_player_assignments,
        ball_acquisition_list,
    )

    output_vid_frames = top_down_overlay.draw_overlay(
        output_vid_frames,
        player_tracks,
        team_player_assignments,
        H,
    )

    # 9) Save result locally
    local_path = f"output_videos/{vid_name}.mp4"
    save_video(
        output_frames=output_vid_frames,
        output_path=f"output_videos/{vid_name}.mp4",
    )

    # 10) Upload results to minio 
    output_bucket = "basketball-processed"
    upload_video(local_path=local_path, key=key, BUCKET_NAME=output_bucket)

if __name__ == "__main__":
    main()
    