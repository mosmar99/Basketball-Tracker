from utils import read_video, save_video
from tracking import PlayerTracker, BallTracker
from canvas import PlayerTrackDrawer, BallTrackDrawer
from team_assigner import TeamAssigner

def main():
    # read video
    vid_name = "video_3"
    vid_frames = read_video(f"input_videos/{vid_name}.mp4")

    # init tracker
    model_path = "models/ft_best.pt"
    player_tracker = PlayerTracker(model_path=model_path)
    ball_tracker = BallTracker(model_path=model_path)

    # get tracks from videoframes by team
    player_tracks = player_tracker.get_object_tracks(vid_frames,
                                                     read_from_stub=True,
                                                     stub_path="stubs/player_track_stubs.pkl")
    ball_tracks = ball_tracker.get_object_tracks(vid_frames,
                                                 read_from_stub=True,
                                                 stub_path="stubs/ball_track_stubs.pkl")
    team_assigner = TeamAssigner(team_A="RED shirt", team_B="WHITE shirt")
    team_player_assignments = team_assigner.get_player_teams_over_frames(vid_frames, player_tracks, 
                                                                         read_from_stub=True, 
                                                                         stub_path="stubs/player_assignment_stubs.pkl")
    
    # erase wrongly detected basketball tracks & interp. between conservative basketball positions
    ball_tracks = ball_tracker.remove_incorrect_detections(ball_tracks)
    ball_tracks = ball_tracker.interp_ball_pos(ball_tracks) 

    # fill canvas with annotations
    player_tracks_drawer = PlayerTrackDrawer()
    player_vid_frames = player_tracks_drawer.draw_annotations(vid_frames, 
                                                              player_tracks, 
                                                              team_player_assignments)

    ball_track_drawer = BallTrackDrawer()
    output_vid_frames = ball_track_drawer.draw_annotations(player_vid_frames, ball_tracks)

    # save video
    save_video(output_frames=output_vid_frames, output_path=f"output_videos/{vid_name}.avi")

if __name__ == "__main__":
    main()