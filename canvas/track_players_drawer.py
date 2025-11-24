from .utils import draw_triangle, draw_square

class PlayerTrackDrawer: # bgr
    def __init__(self,team_1_color=[83, 168, 52],team_2_color=[244, 133, 66]):
        self.default_player_team_id = 1
        self.team_1_color=team_1_color
        self.team_2_color=team_2_color

    def draw_annotations(self,video_frames,tracks,player_assignment,ball_acquisition_list):
        output_video_frames= []
        for frame_id, frame in enumerate(video_frames):
            frame = frame.copy()

            player_dict = tracks[frame_id]

            player_assignment_for_frame = player_assignment[frame_id]

            id_player_with_ball =  ball_acquisition_list[frame_id]

            for track_id, player in player_dict.items():
                team_id = player_assignment_for_frame.get(track_id, self.default_player_team_id)

                if team_id == 1:
                    color = self.team_1_color
                else:
                    color = self.team_2_color

                if track_id == id_player_with_ball:
                    frame = draw_triangle(frame, player["bbox"], (0, 0, 255))

                frame = draw_square(frame, player["bbox"],color, track_id)

            output_video_frames.append(frame)
        
        return output_video_frames
        