from ultralytics import YOLO
import supervision as sv
import numpy as np
import pandas as pd
import sys
sys.path.append("../")
from utils import read_stub, save_stub

class BallTracker():
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect_frames(self, vid_frames, batch_size=20, min_conf=0.5):
        detections = []
        for i in range(0, len(vid_frames), batch_size):
            batch_frames = vid_frames[i:i+batch_size]
            batch_detections = self.model.predict(batch_frames, conf=min_conf)
            detections += batch_detections
        return detections
    
    def get_object_tracks(self, vid_frames, read_from_stub=False, stub_path=None):
        tracks = read_stub(read_from_stub, stub_path)
        if tracks is not None:
            if len(tracks) == len(vid_frames):
                return tracks

        detections = self.detect_frames(vid_frames)
        
        tracks = []
        for frame_id, detection in enumerate(detections):
            class_names =  detection.names
            class_names_inv = {val:key for key,val in class_names.items()}  
            detection_sv = sv.Detections.from_ultralytics(detection)
            tracks.append({})
            
            # pick the basketball bbox with the highest conf.
            picked_bbox = None
            max_conf = 0
            for frame_detection in detection_sv:
                bbox = frame_detection[0].tolist()
                class_id = frame_detection[3]
                conf = frame_detection[2]

                if class_id == class_names_inv["Ball"]:
                    if max_conf < conf:
                        picked_bbox = bbox
                        max_conf = conf
            if picked_bbox is not None:
                tracks[frame_id][1] = {"bbox": picked_bbox}

        save_stub(stub_path, tracks)
        return tracks
    
    def remove_incorrect_detections(self, ball_positions):
        max_permitted_pixel_dist = 25
        prev_good_frame_idx = -1

        for i in range(len(ball_positions)):
            curr_bbox = ball_positions[i].get(1, {}).get("bbox", [])
            # no detected basketball
            if len(curr_bbox) == 0:
                continue
            # first detection of basketball
            if prev_good_frame_idx == -1:
                prev_good_frame_idx = i
                continue
            prev_good_bbox = ball_positions[prev_good_frame_idx].get(1, {}).get("bbox", [])
            frame_gap = i - prev_good_frame_idx
            adjusted_max_dist = max_permitted_pixel_dist * frame_gap
            if np.linalg.norm(np.array(prev_good_bbox[:2]) - np.array(curr_bbox[:2])) > adjusted_max_dist:
                ball_positions[i] = {}
            else:
                prev_good_frame_idx = i

        return ball_positions
    
    def interp_ball_pos(self, ball_positions):
        ball_positions = [pos.get(1, {}).get("bbox", []) for pos in ball_positions]
        df_ball_positions = pd.DataFrame(ball_positions, columns=["x1", "y1", "x2", "y2"])
        df_ball_positions = df_ball_positions.interpolate()
        df_ball_positions = df_ball_positions.bfill()
        ball_positions = [{1:{"bbox": pos}} for pos in df_ball_positions.to_numpy().tolist()]
        return ball_positions