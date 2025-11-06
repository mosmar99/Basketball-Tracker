from utils import read_video, save_video
from tracking import PlayerTracker

def main():
    # read video
    vid_name = "video_1"
    vid_frames = read_video(f"input_videos/{vid_name}.mp4")

    # init tracker
    player_tracker = PlayerTracker(model_path="models/ft_best.pt")

    # get tracks from videoframes
    player_tracks = player_tracker.get_object_tracks(vid_frames,
                                                     read_from_stub=True,
                                                     stub_path="stubs/player_track_stubs.pkl")
    print(player_tracks)

    # save video
    save_video(output_frames=vid_frames, output_path=f"output_videos/{vid_name}.avi")

if __name__ == "__main__":
    main()