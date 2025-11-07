from .utils import draw_ellipse

class PlayerTrackDrawer:

    def __init__(self):
        pass

    def draw_annotations(self, vid_frames, tracks):
        output_vid_frames = []

        for frame_id, frame in enumerate(vid_frames):
            frame = frame.copy()

            player_dict = tracks[frame_id]

            # render player tracks
            for track_id, player in player_dict.items():
                frame = draw_ellipse(frame, player['bbox'], (255,0,0), track_id)
            
            output_vid_frames.append(frame)
        
        return output_vid_frames