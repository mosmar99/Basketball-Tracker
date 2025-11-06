import os
import cv2

def read_video(video_path):
    capture = cv2.VideoCapture(video_path)
    frames = []
    while True:
        returned, frame = capture.read()
        if not returned:
            break
        frames.append(frame)
    return frames

def save_video(output_frames, output_path):
    if not os.path.exists(os.path.dirname(output_path)):
        os.mkdir(os.path.dirname(output_path))
    
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    (frame_width, frame_height) = (output_frames[0].shape[1], output_frames[0].shape[0])
    out = cv2.VideoWriter(output_path, fourcc, 24.0, (frame_width, frame_height))

    for frame in output_frames:
        out.write(frame)
    
    out.release()


