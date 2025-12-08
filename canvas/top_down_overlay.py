import cv2
import numpy as np

class TDOverlay:
    def __init__(self, ref, minimap, t1_color = [83, 168, 52], t2_color = [244, 133, 66], xz=300, yz=170):
        self.minimap_w = xz
        self.minimap_h = yz

        self.video_area = xz * yz

        self.ref = cv2.imread(ref)
        self.ref_w, self.ref_h = self.ref.shape[:2]

        self.minimap = cv2.imread(minimap)
        self.minimap = cv2.resize(self.minimap, (self.minimap_w, self.minimap_h), interpolation=cv2.INTER_LINEAR)

        self.color = {1: t1_color, 2: t2_color}

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

    def draw_voronoi(self, minimap, subdiv, teams, alpha=0.2):
        facets, _ = subdiv.getVoronoiFacetList([])
        vor_minimap = minimap.copy()
        frame_control = {1: 0, 2: 0}

        boundary_poly = np.array([
            [0, 0], 
            [self.minimap_w, 0], 
            [self.minimap_w, self.minimap_h], 
            [0, self.minimap_h]
        ], dtype=np.float32)

        for facet, t in zip(facets, teams):
            facet = np.array(facet, dtype=np.int32)

            intersection_area, _ = cv2.intersectConvexConvex(facet, boundary_poly)
            frame_control[t] += intersection_area / self.video_area

            cv2.fillConvexPoly(vor_minimap, facet, self.color[t], lineType=cv2.LINE_AA)
            cv2.polylines(vor_minimap, [facet], True, (0, 0, 0), 2, lineType=cv2.LINE_AA)

        result = cv2.addWeighted(vor_minimap, alpha, minimap, 1-alpha, 0)
        return result, frame_control
    
    def draw_players(self, minimap, positions, teams):
        for (mx, my), t in zip(positions, teams):
            cv2.circle(minimap, (mx, my), 10, self.color[t], -1)
            cv2.circle(minimap, (mx, my), 10, (0, 0, 0), 2, lineType=cv2.LINE_AA)
        return minimap
    
    def draw_overlay(self, frames, td_track, x=0, y=0):
        res = []
        control = []
        for frame_idx, td_frame in enumerate(td_track):
            frame = frames[frame_idx].copy()
            minimap_frame = self.minimap.copy()

            subdiv = cv2.Subdiv2D((0, 0, self.minimap_w, self.minimap_h))
            team = []
            positions = []

            for _, player in td_frame.items():
                px, py = player["pos"]
                mx, my = int(px*self.minimap_w), int(py*self.minimap_h)

                mx = max(0, min(mx, self.minimap_w - 1))
                my = max(0, min(my, self.minimap_h - 1))

                team_id = player["team_id"]

                subdiv.insert((mx, my))
                positions.append((mx, my))
                team.append(team_id)
            
            minimap_frame, frame_control = self.draw_voronoi(minimap_frame, subdiv, team)
            minimap_frame = self.draw_players(minimap_frame, positions, team)
            
            frame[x:self.minimap_h, y:self.minimap_w] = minimap_frame
            control.append(frame_control)
            res.append(frame)

        return res, control