from utils import read_video, save_video
from tracking import PlayerTracker, BallTracker, get_production_model_path
from canvas import PlayerTrackDrawer, BallTrackDrawer, BallPossessionDrawer
from team_assigner import TeamAssigner
from ball_acq import BallAcquisitionSensor
from shared import download_to_temp, upload_video

def main():
    # --- 1) Identify video in MinIO ---
    vid_name = "video_1"
    bucket = "basketball-raw-videos"              
    key = f"{vid_name}.mp4"

    # --- 2) Download from MinIO to a temp file ---
    tmp_video_path = download_to_temp(key=key, bucket=bucket)

    # --- 3) Read frames from that temp file (same as before) ---
    vid_frames = read_video(tmp_video_path)

    # --- 4) Init trackers (unchanged) ---
    model_path = get_production_model_path()
    player_tracker = PlayerTracker(model_path=model_path)
    ball_tracker = BallTracker(model_path=model_path)

    # --- 5) Tracking (unchanged) ---
    player_tracks = player_tracker.get_object_tracks(
        vid_frames,
        read_from_stub=True,
        stub_path="stubs/player_track_stubs.pkl",
    )
    ball_tracks = ball_tracker.get_object_tracks(
        vid_frames,
        read_from_stub=True,
        stub_path="stubs/ball_track_stubs.pkl",
    )

    team_assigner = TeamAssigner(team_A="WHITE shirt", team_B="DARK BLUE shirt")
    team_player_assignments = team_assigner.get_player_teams_over_frames(
        vid_frames,
        player_tracks,
        read_from_stub=True,
        stub_path="stubs/player_assignment_stubs.pkl",
    )

    # --- 6) Ball acquisition + ball track cleanup (unchanged) ---
    ball_acquisition_sensor = BallAcquisitionSensor()
    ball_acquisition_list = ball_acquisition_sensor.detect_ball_possession(
        player_tracks, ball_tracks
    )

    ball_tracks = ball_tracker.remove_incorrect_detections(ball_tracks)
    ball_tracks = ball_tracker.interp_ball_pos(ball_tracks)

    # --- 7) Draw overlays (unchanged) ---
    player_tracks_drawer = PlayerTrackDrawer()
    ball_track_drawer = BallTrackDrawer()
    ball_possession_drawer = BallPossessionDrawer()

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

    # --- 8) Save result locally ---
    local_path = f"output_videos/{vid_name}.mp4"
    save_video(
        output_frames=output_vid_frames,
        output_path=f"output_videos/{vid_name}.mp4",
    )

    # --- 9) Upload results to minio --- 
    output_bucket = "basketball-processed"
    upload_video(local_path=local_path, key=key, BUCKET_NAME=output_bucket)

if __name__ == "__main__":
    main()
    