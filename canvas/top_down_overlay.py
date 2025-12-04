import cv2
import numpy as np

class TDOverlay:
    def __init__(self, ref, minimap, t1_color = [83, 168, 52], t2_color = [244, 133, 66], xz=300, yz=170):
        self.minimap_w = xz
        self.minimap_h = yz

        self.ref = cv2.imread(ref)
        self.ref_w, self.ref_h = self.ref.shape[:2]

        self.minimap = cv2.imread(minimap)
        self.minimap = cv2.resize(self.minimap, (self.minimap_w, self.minimap_h), interpolation=cv2.INTER_LINEAR)

        self.t1_color = t1_color
        self.t2_color = t2_color

        self.default_player_team_id = None

    def get_td_tracks(self, player_tracks, team_player_assignments, H):
        topdown = []
        for frame_idx in range(len(player_tracks)):
            if H[frame_idx] == None:
                topdown.append({})
                continue
            players = player_tracks[frame_idx]
            player_teams = team_player_assignments[frame_idx]
            
            frame = {}
            for track_id, player in players.items():
                x1, _, x2, y2 = player["bbox"]

                bx = (x1 + x2) / 2
                by = y2
                p = np.array([bx, by, 1.0], dtype=np.float32)

                wp = H[frame_idx] @ p
                wp /= wp[2]

                px = wp[0] / self.ref.shape[1]
                py = wp[1] / self.ref.shape[0]

                pos = (px, py)
                team_id = player_teams.get(track_id, self.default_player_team_id)
                frame[track_id] = {"pos": pos, "team_id": team_id}

            topdown.append(frame)

        return topdown

    def draw_voronoi(self, minimap, subdiv, colors, alpha=0.2):
        facets, _ = subdiv.getVoronoiFacetList([])
        vor_minimap = minimap.copy()

        for facet, color in zip(facets, colors):
            facet = np.array(facet, dtype=np.int32)

            cv2.fillConvexPoly(vor_minimap, facet, color, lineType=cv2.LINE_AA)
            cv2.polylines(vor_minimap, [facet], True, (0, 0, 0), 1, lineType=cv2.LINE_AA)
        
        result = cv2.addWeighted(vor_minimap, alpha, minimap, 1-alpha, 0)
        return result
    
    def draw_players(self, minimap, positions, colors):
        for (mx, my), color in zip(positions, colors):
            cv2.circle(minimap, (mx, my), 6, color, -1)
        return minimap
    
    def draw_overlay(self, frames, td_track, x=0, y=0):
        res = []
        for frame_idx, td_frame in enumerate(td_track):
            frame = frames[frame_idx].copy()
            minimap_frame = self.minimap.copy()

            subdiv = cv2.Subdiv2D((0, 0, self.minimap_w, self.minimap_h))
            colors = []
            positions = []

            for _, player in td_frame.items():
                px, py = player["pos"]
                mx, my = int(px*self.minimap_w), int(py*self.minimap_h)

                mx = max(0, min(mx, self.minimap_w - 1))
                my = max(0, min(my, self.minimap_h - 1))

                team_id = player["team_id"]
                color = self.t1_color if team_id == 1 else self.t2_color

                subdiv.insert((mx, my))
                positions.append((mx, my))
                colors.append(color)
            
            minimap_frame = self.draw_voronoi(minimap_frame, subdiv, colors)
            minimap_frame = self.draw_players(minimap_frame, positions, colors)
            
            frame[x:self.minimap_h, y:self.minimap_w] = minimap_frame
            res.append(frame)

        return res