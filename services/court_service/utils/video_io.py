import cv2

def load_frames(video_path, sample_rate=10):
    cap = cv2.VideoCapture(video_path)
    frames = []
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % sample_rate == 0:
            frames.append(frame)
        count += 1
    cap.release()
    print(f"[INFO] Loaded {len(frames)} frames.")
    return frames