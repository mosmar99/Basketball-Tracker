import cv2
import numpy as np

class TDOverlay:
    def __init__(self, ref, minimap, t1_color = [83, 168, 52], t2_color = [244, 133, 66]):
        self.minimap_w = 300
        self.minimap_h = 170

        self.ref = cv2.imread(ref)
        self.ref_w, self.ref_h = self.ref.shape[:2]

        self.minimap = cv2.imread(minimap)
        self.minimap = cv2.resize(self.minimap, (self.minimap_w, self.minimap_h), interpolation=cv2.INTER_LINEAR)

        self.t1_color = t1_color
        self.t2_color = t2_color

        self.default_player_team_id = None

    def draw_overlay(self, frames, player_tracks, team_player_assignments, H):
        res = []
        for frame_idx in range(len(frames)):
            frame = frames[frame_idx].copy()
            players = player_tracks[frame_idx]
            player_teams = team_player_assignments[frame_idx]
            minimap_frame = self.minimap.copy()

            for track_id, player in players.items():
                x1, _, x2, y2 = player["bbox"]

                bx = (x1 + x2) / 2
                by = y2
                p = np.array([bx, by, 1.0], dtype=np.float32)

                wp = H[frame_idx] @ p
                wp /= wp[2]

                mx = int(wp[0] * self.minimap_w / self.ref.shape[1])
                my = int(wp[1] * self.minimap_h / self.ref.shape[0])

                team_id = player_teams.get(track_id, self.default_player_team_id)

                if team_id == 1:
                    color = self.t1_color
                else:
                    color = self.t2_color

                cv2.circle(minimap_frame, (mx, my), 6, color, -1)
            
            frame[0:self.minimap_h, 0:self.minimap_w] = minimap_frame
            res.append(frame)

        return res