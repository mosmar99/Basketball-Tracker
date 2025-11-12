from .utils import draw_triangle

class BallTrackDrawer():
    def __init__(self):
        self.ball_pntr_color = (0, 255, 0)

    def draw_annotations(self, vid_frames, tracks):
        output_video_frames = []
        for frame_id, frame in enumerate(vid_frames):
            output_frame = frame.copy()
            ball_dict = tracks[frame_id]
            for _, track in ball_dict.items():
                bbox = track["bbox"]
                if bbox is None:
                    continue
                output_frame = draw_triangle(frame, bbox, self.ball_pntr_color)
            output_video_frames.append(output_frame)
        return output_video_frames