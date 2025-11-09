import numpy as np
import sys
sys.path.append("../")
from utils import get_straight_line_distance, get_center_bbox

class BallAcquisitionSensor():
    def __init__(self):
        self.possession_threshold = 50 # max distance from player
        self.min_ball_frames = 4 # min X frames intersection with a persons boundary to consider acquision
        self.containment_threshold_IoU = 0.8 # if ball is overlapping by a player to 80 %, consider that a ball acquisition

    def get_bbox_assignment_points(self, player_bbox, ball_center):
        ball_center_x, ball_center_y = ball_center[0], ball_center[1]
        x1,y1,x2,y2 = player_bbox
        # check which border of the player_bbox that the ball is the closest to
        output_points = []
        if ball_center_y > y1 and ball_center_y < y2:
            output_points.append((x1, ball_center_y))
            output_points.append((x2, ball_center_y))
        if ball_center_x > x1 and ball_center_x < x2:
            output_points.append((ball_center_x, y1))
            output_points.append((ball_center_x, y2))
        output_points += {
            (x1,y1), #top-left
            (x1+int(0.5*(x2-x1)),y1), #top_mid
            (x2,y1), #top-right
            (x2,y1+int(0.5*(y2-y1))), #right_mid
            (x2,y2), #bottom-right
            (x1+int(0.5*(x2-x1)),y2), #bottom_mid
            (x1,y2), #bottom-left
            (x1,y1+int(0.5*(y2-y1))), #left_mid
        }

        return output_points
    
    def find_min_dist_to_ball(self, player_bbox, ball_center):
        key_points = self.get_bbox_assignment_points(player_bbox, ball_center)
        min_dist = min(get_straight_line_distance(key_point, ball_center) for key_point in key_points)
        return min_dist 

    def calculate_containment_IoU(self, player_bbox, ball_bbox):
        px1,py1,px2,py2 = player_bbox
        bx1,by1,bx2,by2 = ball_bbox
        ball_area = (bx2-bx1)*(by2-by1)

        inter_x1 = max(px1, bx1)
        inter_y1 = max(py1, by1)
        inter_x2 = min(px2, bx2)
        inter_y2 = min(py2, by2)

        intersection = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)

        ball_iou = intersection / ball_area
        return ball_iou
    
    def find_best_player_for_ball(self, player_tracks_by_frame, ball_center, ball_bbox):
        high_iou_players = []
        regular_dist_players = []

        for player_id, player_annotations in player_tracks_by_frame.items():
            player_bbox = player_annotations.get("bbox", [])
            if not player_bbox:
                continue
            containment_iou = self.calculate_containment_IoU(player_bbox, ball_bbox)
            min_dist = self.find_min_dist_to_ball(player_bbox, ball_center)

            if containment_iou >= self.containment_threshold_IoU:
                high_iou_players.append((player_id, containment_iou))
            elif min_dist <= self.possession_threshold:
                regular_dist_players.append((player_id, min_dist))
        
        if high_iou_players:
            best_player = max(high_iou_players, key=lambda x: x[1])[0]
        elif regular_dist_players:
            best_player = min(regular_dist_players, key=lambda x: x[1])[0]
        else:
            best_player = -1

        return best_player
    
    def detect_ball_possession(self, player_tracks, ball_tracks):
        num_frames = len(ball_tracks)
        ball_possessions = [-1] * num_frames
        consecutive_possession_counts = {}

        for frame_id in range(num_frames):
            ball_annotation = ball_tracks[frame_id].get(1, {}) # there is only one ball with id 1
            if not ball_annotation:
                continue

            ball_bbox = ball_annotation.get("bbox", [])
            if not ball_bbox:
                continue

            ball_center = get_center_bbox(ball_bbox)
            best_player_id = self.find_best_player_for_ball(player_tracks[frame_id], ball_center, ball_bbox)

            if best_player_id != -1:
                number_of_consecutive_frames = consecutive_possession_counts.get(best_player_id, 0) + 1 # incr the #frames the player had
                consecutive_possession_counts = {best_player_id : number_of_consecutive_frames}

                if consecutive_possession_counts[best_player_id] >= self.min_ball_frames:
                    ball_possessions[frame_id] = best_player_id

            else:
                consecutive_possession_counts = {}

        # post-process to fill in gaps in ball possession
        arr = np.array(ball_possessions, dtype=int)
        valid = np.where(arr != -1)[0]
        [arr.__setitem__(slice(a, b + 1), arr[a]) for a, b in zip(valid, valid[1:]) if arr[a] == arr[b]]
        ball_possessions = arr.tolist()

        return ball_possessions

