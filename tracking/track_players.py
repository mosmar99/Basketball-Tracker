from ultralytics import YOLO
import supervision as sv
import sys
sys.path.append("../")
from utils import read_stub, save_stub

class PlayerTracker():
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()

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
            detection_with_tracks = self.tracker.update_with_detections(detection_sv)
            
            tracks.append({})

            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                class_id = frame_detection[3]
                track_id = frame_detection[4]

                if class_id == class_names_inv["Player"]:
                    tracks[frame_id][track_id] = {"bbox": bbox}

        save_stub(stub_path, tracks)
        return tracks
              

