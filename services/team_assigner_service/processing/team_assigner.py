import cv2
import numpy as np
from PIL import Image
from collections import defaultdict
from sklearn.cluster import KMeans

import sys 
sys.path.append('../')

class TeamAssigner:
    def __init__(self, crop_factor = 0.3):
        self.crop_factor = crop_factor

    def get_center_crop(self, img_array, crop_factor=0.4, skew_factor=0.1):
        h, w, _ = img_array.shape
        h_center, w_center = h // 2, w // 2
        h_crop, w_crop = int(h * crop_factor), int(w * crop_factor)
        h_skew = int(h * skew_factor)

        y1 = max(0, h_center - h_crop // 2 - h_skew)
        y2 = min(h, h_center + h_crop // 2 - h_skew)
        x1 = max(0, w_center - w_crop // 2)
        x2 = min(w, w_center + w_crop // 2)
        
        return img_array[y1:y2, x1:x2]
    
    def _extract_features(self, pil_images):
        features = []
        bins = (8, 4, 4) 
        
        for pil in pil_images:
            img = np.array(pil)
            img_crop = self.get_center_crop(img, crop_factor=self.crop_factor)

            hsv = cv2.cvtColor(img_crop, cv2.COLOR_RGB2HSV)

            hist = cv2.calcHist([hsv], [0, 1, 2], None, bins, [0, 180, 0, 256, 0, 256])
            cv2.normalize(hist, hist)

            features.append(hist.flatten())

        return np.array(features)

    def get_rgb_from_histogram(self, hist_vector, bins=(8, 4, 4)):
        hist_3d = hist_vector.reshape(bins)

        h_idx, s_idx, v_idx = np.unravel_index(np.argmax(hist_3d), bins)

        h_step = 180.0 / bins[0]
        s_step = 256.0 / bins[1]
        v_step = 256.0 / bins[2]

        h_val = int(h_idx * h_step + h_step / 2)
        s_val = int(s_idx * s_step + s_step / 2)
        v_val = int(v_idx * v_step + v_step / 2)

        hsv_pixel = np.array([[[h_val, s_val, v_val]]], dtype=np.uint8)
        rgb_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2RGB)[0][0]

        return tuple(map(int, rgb_pixel))
    
    def get_player_teams_global(self, vid_frames, player_tracks):
        player_features_map = defaultdict(list)
        frame_assignments = [dict() for _ in range(len(vid_frames))]

        for frame_id, player_track in enumerate(player_tracks):
            frame = vid_frames[frame_id]
            
            frame_crops = []
            frame_pids = []

            for pid, info in player_track.items():
                x1, y1, x2, y2 = map(int, info['bbox'])
                crop = frame[y1:y2, x1:x2]

                pil_img = Image.fromarray(crop)
                
                frame_crops.append(pil_img)
                frame_pids.append(pid)

            if not frame_crops:
                continue

            feats = self._extract_features(frame_crops)
            
            for pid, feat in zip(frame_pids, feats):
                player_features_map[pid].append(feat)
        
        unique_pids = list(player_features_map.keys())
        averaged_features = []

        for pid in unique_pids:
            # Average features per player id for global embedding (Remove noise)
            if len(player_features_map[pid]) > 3: # Id should exist for atleast this number of frames to be used in kmeans
                feats = np.array(player_features_map[pid])
                avg_feat = np.mean(feats, axis=0)
                averaged_features.append(avg_feat)
            else:
                averaged_features.append(averaged_features[-1])

        if not unique_pids:
            return frame_assignments

        print(f" # Player ID's: {len(unique_pids)}")
        
        kmeans = KMeans(n_clusters=2, random_state=42)
        
        if len(unique_pids) >= 2:
            labels = kmeans.fit_predict(averaged_features)

            team1_color = self.get_rgb_from_histogram(kmeans.cluster_centers_[0], bins=(8, 4, 4))
            team2_color = self.get_rgb_from_histogram(kmeans.cluster_centers_[1], bins=(8, 4, 4))
            team_colors = {1: team1_color, 2: team2_color}
        else:
            labels = [1] * len(unique_pids) # Fallback in case of not enough players
            team_colors = {1: (255, 255, 255), 2: (0, 0, 0)}

        pid_to_team = {pid: int(label) + 1 for pid, label in zip(unique_pids, labels)}

        for frame_id, player_track in enumerate(player_tracks):
            for pid in player_track.keys():
                if pid in pid_to_team:
                    team_id = pid_to_team[pid]
                    frame_assignments[frame_id][pid] = team_id

        return frame_assignments, team_colors

    def get_player_teams_over_frames(self, vid_frames, player_tracks):
        return self.get_player_teams_global(vid_frames, player_tracks)