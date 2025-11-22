from utils import read_video, save_video
from tracking import PlayerTracker, BallTracker, get_production_model_path
from canvas import PlayerTrackDrawer, BallTrackDrawer, BallPossessionDrawer
from team_assigner import TeamAssigner
from ball_acq import BallAcquisitionSensor
from shared import download_to_temp, upload_video

import requests

def get_tracks_from_service(local_video_path: str):
    url = "http://localhost:8000/track"
    with open(local_video_path, "rb") as f:
        files = {"file": (local_video_path, f, "video/mp4")}
        r = requests.post(url, files=files)
    r.raise_for_status()
    data = r.json()
    return data["player_tracks"], data["ball_tracks"]

def deserialize_tracks(serialized):
    """
    Inverse of serialize_tracks():
    [
      [ {"track_id": int, "bbox": [..]}, ... ],   # frame 0
      [ {...}, ... ],                             # frame 1
      ...
    ]
    -> 
    [
      {track_id: {"bbox": [...]}, ...},          # frame 0
      {track_id: {"bbox": [...]}, ...},          # frame 1
      ...
    ]
    """
    tracks = []
    for frame in serialized:
        frame_dict = {}
        for obj in frame:
            track_id = int(obj["track_id"])
            bbox = obj.get("bbox", [])
            frame_dict[track_id] = {"bbox": bbox}
        tracks.append(frame_dict)
    return tracks

def main():
    # --- 1) Identify video in MinIO ---
    vid_name = "video_1"
    bucket = "basketball-raw-videos"              
    key = f"{vid_name}.mp4"

    # --- 2) Download from MinIO to a temp file ---
    tmp_video_path = download_to_temp(key=key, bucket=bucket)

    # --- 3) Read frames from that temp file (same as before) ---
    vid_frames = read_video(tmp_video_path)

    # # model_path = get_production_model_path()
    # model_path = "models/prod/ft_best.pt"
    # print("> model_path=", model_path)
    # player_tracker = PlayerTracker(model_path=model_path)
    # ball_tracker = BallTracker(model_path=model_path)

    # player_tracks = player_tracker.get_object_tracks(
    #     vid_frames,
    #     read_from_stub=False,
    #     stub_path="stubs/player_track_stubs.pkl",
    # )
    # ball_tracks = ball_tracker.get_object_tracks(
    #     vid_frames,
    #     read_from_stub=False,
    #     stub_path="stubs/ball_track_stubs.pkl",
    # )

    player_tracks_json, ball_tracks_json = get_tracks_from_service(tmp_video_path)
    player_tracks = deserialize_tracks(player_tracks_json)
    ball_tracks = deserialize_tracks(ball_tracks_json)

    team_assigner = TeamAssigner(team_A="WHITE shirt", team_B="DARK BLUE shirt")
    team_player_assignments = team_assigner.get_player_teams_over_frames(
        vid_frames,
        player_tracks,
        read_from_stub=True,
        stub_path="stubs/player_assignment_stubs.pkl",
    )

    # # --- 6) Ball acquisition + ball track cleanup (unchanged)
    # ball_acquisition_sensor = BallAcquisitionSensor()
    # ball_acquisition_list = ball_acquisition_sensor.detect_ball_possession(
    #     player_tracks, ball_tracks
    # )

    # ball_tracks = ball_tracker.remove_incorrect_detections(ball_tracks)
    # ball_tracks = ball_tracker.interp_ball_pos(ball_tracks)

    # # --- 7) Draw overlays (unchanged) ---
    # player_tracks_drawer = PlayerTrackDrawer()
    # ball_track_drawer = BallTrackDrawer()
    # ball_possession_drawer = BallPossessionDrawer()

    # player_vid_frames = player_tracks_drawer.draw_annotations(
    #     vid_frames,
    #     player_tracks,
    #     team_player_assignments,
    #     ball_acquisition_list,
    # )

    # output_vid_frames = ball_track_drawer.draw_annotations(
    #     player_vid_frames,
    #     ball_tracks,
    # )

    # output_vid_frames = ball_possession_drawer.draw_ball_possession(
    #     output_vid_frames,
    #     team_player_assignments,
    #     ball_acquisition_list,
    # )

    # # --- 8) Save result locally ---
    # local_path = f"output_videos/{vid_name}.mp4"
    # save_video(
    #     output_frames=output_vid_frames,
    #     output_path=f"output_videos/{vid_name}.mp4",
    # )

    # # --- 9) Upload results to minio --- 
    # output_bucket = "basketball-processed"
    # upload_video(local_path=local_path, key=key, BUCKET_NAME=output_bucket)

if __name__ == "__main__":
    main()
    