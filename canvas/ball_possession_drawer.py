import cv2
import numpy as np

class BallPossessionDrawer:
    def __init__(self):
        pass

    def get_team_ball_possession(self, team_player_assignments, ball_acquisition_list):
        team_ball_possession = []
        for team_player_assignment_frame, ball_acquisition_frame in zip(team_player_assignments, ball_acquisition_list):
            if ball_acquisition_frame == -1:
                team_ball_possession.append(-1)
                continue
            if ball_acquisition_frame not in team_player_assignment_frame:
                team_ball_possession.append(-1)
                continue

            if team_player_assignment_frame[ball_acquisition_frame] == 1:
                team_ball_possession.append(1)
            else:
                team_ball_possession.append(2)

        return np.array(team_ball_possession)

    def draw_ball_possession(self, vid_frames, team_player_assignments, ball_acquisition_list):
        team_ball_possession = self.get_team_ball_possession(team_player_assignments, ball_acquisition_list)
        output_vid_frames = []
        for frame_id, frame in enumerate(vid_frames):
            if frame_id == 0:
                output_vid_frames.append(frame)
                continue
            frame_drawn = self.draw_frame(frame, frame_id, team_ball_possession)
            output_vid_frames.append(frame_drawn)
        return output_vid_frames
    
    def draw_frame(self, frame, frame_id, team_ball_possession):
        possession_stats_window = frame.copy()
        font_scale = 1
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2

        # overlay position
        frame_height, frame_width = frame.shape[0], frame.shape[1]
        rect_x1 = int(frame_width * 0.01)
        rect_y1 = int(frame_height * 0.82)
        rect_x2 = int(frame_width * 0.42)
        rect_y2 = int(frame_height * 0.95)

        # text position
        text_x = int(frame_width * 0.02)
        text_y1 = int(frame_height * 0.86)
        text_y2 = int(frame_height * 0.94)

        # draw rectangle
        cv2.rectangle(possession_stats_window, (rect_x1, rect_y1), (rect_x2, rect_y2), (50, 50, 50), cv2.FILLED)
        alpha = 0.8
        cv2.addWeighted(possession_stats_window, alpha, frame, 1 - alpha, 0, frame) 

        team_ball_possession_till_frame = team_ball_possession[:frame_id + 1]
        team_1_possession = np.sum(team_ball_possession_till_frame == 1)
        team_2_possession = np.sum(team_ball_possession_till_frame == 2)
        total_possession = team_1_possession + team_2_possession
        
        if total_possession == 0:
            team_1_percent = 0
            team_2_percent = 0
        else:
            team_1_percent = (team_1_possession / total_possession) * 100
            team_2_percent = (team_2_possession / total_possession) * 100

        cv2.putText(frame, f"Team A | Ball Possession: {team_1_percent:.0f}%", (text_x, text_y1), font, font_scale, (255, 255, 255), thickness)
        cv2.putText(frame, f"Team B | Ball Possession: {team_2_percent:.0f}%", (text_x, text_y2), font, font_scale, (255, 255, 255), thickness)

        return frame