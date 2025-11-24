from ultralytics import YOLO
import supervision as sv
import sys
from ultralytics import SAM
import numpy as np
import random

sys.path.append("../")

class PlayerTracker():
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.tracker = sv.ByteTrack()
        self.sam2 = SAM("sam2.1_b.pt")

        self.max_players = 10
        self.id_map = {}
        self.available_ids = list(range(1, 11))
        self.last_active_small_ids = set()  

    def detect_frames(self, vid_frames, batch_size=20, min_conf=0.5):
        detections = []
        for i in range(0, len(vid_frames), batch_size):
            batch_frames = vid_frames[i:i+batch_size]
            batch_detections = self.model.predict(batch_frames, conf=min_conf)
            detections += batch_detections
        return detections
    
    def mask_to_bbox(self, mask):
        ys, xs = np.where(mask > 0)
        if len(xs) == 0 or len(ys) == 0:
            return [0, 0, mask.shape[1], mask.shape[0]]
        
        x_min = int(xs.min())
        x_max = int(xs.max())
        y_min = int(ys.min())
        y_max = int(ys.max())
        
        return [x_min, y_min, x_max, y_max]
    
    def remap_id(self, byte_id):
        if byte_id in self.id_map:
            return self.id_map[byte_id]

        # fail safe
        if not self.available_ids:
            random_id = random.randint(11,100)
            return random_id

        small_id = self.available_ids.pop(0)
        self.id_map[byte_id] = small_id
        return small_id
    
    def release_id(self, byte_id):
        if byte_id in self.id_map:
            freed = self.id_map.pop(byte_id)
            self.available_ids.append(freed)
            self.available_ids.sort()

    def get_object_tracks(self, vid_frames):
        
        detections = self.detect_frames(vid_frames)

        tracks = []
        total = len(vid_frames)
        for frame_id, frame in enumerate(vid_frames):
            print(f"frame {frame_id}/{total}")
            detection = detections[frame_id]
            class_names =  detection.names
            class_names_inv = {val:key for key,val in class_names.items()}  
            detection_sv = sv.Detections.from_ultralytics(detection)

            refined_bboxes = []
            for det in detection_sv:
                bbox_array = det[0]
                x1, y1, x2, y2 = map(int, bbox_array)
                conf = float(det[2])
                class_id = int(det[3])

                if class_names_inv['Player'] != class_id:
                    continue  # skip non-player detections

                player_crop = frame[y1:y2, x1:x2]

                # SAM2 mask
                results = self.sam2(player_crop, bboxes=[[0,0,x2-x1, y2-y1]])
                mask = results[0].masks.data[0].cpu().numpy().astype(np.uint8)

                x_min_rel, y_min_rel, x_max_rel, y_max_rel = self.mask_to_bbox(mask)

                x1_ref = x1 + x_min_rel
                y1_ref = y1 + y_min_rel
                x2_ref = x1 + x_max_rel
                y2_ref = y1 + y_max_rel

                refined_bboxes.append([x1_ref, y1_ref, x2_ref, y2_ref, conf, class_id])

            xyxy = np.array([b[:4] for b in refined_bboxes])
            confidences = np.array([b[4] for b in refined_bboxes])
            class_ids = np.array([b[5] for b in refined_bboxes])
            detections_sv = sv.Detections(xyxy=xyxy, confidence=confidences, class_id=class_ids)
            detection_with_tracks = self.tracker.update_with_detections(detections_sv)
            tracks.append({})

            current_ids = set()

            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                class_id = frame_detection[3]
                track_id = frame_detection[4]

                if class_id == class_names_inv["Player"]:
                    small_id = self.remap_id(track_id)
                    if small_id is None:
                        continue

                    current_ids.add(small_id)

                if class_id == class_names_inv["Player"]:
                    tracks[frame_id][small_id] = {"bbox": bbox}
            
            lost_ids = self.last_active_small_ids - current_ids
            for lost_small_id in lost_ids:
                byte_ids_to_release = [b for b, s in self.id_map.items() if s == lost_small_id]
                for b in byte_ids_to_release:
                    self.release_id(b)

            self.last_active_small_ids = current_ids

        return tracks
              

