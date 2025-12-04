import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from shared.storage import upload_video

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
    dir_name = os.path.dirname(output_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    frame_height, frame_width = output_frames[0].shape[0], output_frames[0].shape[1]
    out = cv2.VideoWriter(output_path, fourcc, 24.0, (frame_width, frame_height))

    for frame in output_frames:
        out.write(frame)

    out.release()

def save_ball_heatmap(heatmap, video_name):
    os.makedirs("temp_ball_vid", exist_ok=True)

    png_path = f"temp_ball_vid/{video_name}_heatmap.png"

    plt.imshow(heatmap, cmap="hot")
    plt.colorbar()
    plt.savefig(png_path, dpi=300)
    plt.close()

    key_png = f"ball_heatmap/{video_name}.png"

    upload_video(png_path, key_png, BUCKET_NAME="figures")

    try:
        os.remove(png_path)
    except:
        pass


def save_ball_overlay_video(frames, video_name):
    os.makedirs("videos/ball_heatmap", exist_ok=True)

    tmp_raw = f"{video_name}_raw_tmp.mp4"
    final_path = f"videos/ball_heatmap/{video_name}.mp4"

    save_video(frames, tmp_raw)

    os.system(
        f"ffmpeg -y -i {tmp_raw} -vcodec libx264 -preset fast -movflags +faststart {final_path}"
    )

    key = f"ball_heatmap/{video_name}.mp4"
    upload_video(final_path, key, BUCKET_NAME="videos")

    try:
        os.remove(tmp_raw)
    except:
        pass
