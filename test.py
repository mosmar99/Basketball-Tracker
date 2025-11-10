import cv2
import numpy as np
import glob
from tqdm import tqdm

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

def align_frames_sift(frames, ref_idx=0, ignore_mask=None):
    sift = cv2.SIFT_create()
    matcher = cv2.BFMatcher()
    ref_frame = frames[ref_idx]
    ref_gray = cv2.cvtColor(ref_frame, cv2.COLOR_BGR2GRAY)
    
    # invert mask for OpenCV detectAndCompute() (mask=valid region)
    overlay_mask = None
    if ignore_mask is not None:
        overlay_mask = (1 - ignore_mask).astype(np.uint8)

    kp_ref, des_ref = sift.detectAndCompute(ref_gray, overlay_mask)
    aligned = []
    h, w = ref_frame.shape[:2]

    for i, frame in enumerate(tqdm(frames, desc="[INFO] Aligning frames")):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        kp, des = sift.detectAndCompute(gray, overlay_mask)
    
        matches = matcher.knnMatch(des, des_ref, k=2)

        # Lowe’s ratio test
        good = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good.append(m)

        if len(matches) > 10:
            src_pts = np.float32([kp[m.queryIdx].pt for (m, _) in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_ref[m.trainIdx].pt for (m, _) in matches]).reshape(-1, 1, 2)
            H, inliers = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            if H is not None:
                warped = cv2.warpPerspective(frame, H, (w, h))
                aligned.append(warped)
            else:
                aligned.append(frame)
        else:
            aligned.append(frame)

    return aligned

def create_clean_background(frames):
    print("[INFO] Creating player-free background")
    median_bg = np.median(np.array(frames), axis=0).astype(np.uint8)
    return median_bg

def create_temporal_mask(frames, var_thresh=2.0):
    stack = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames], axis=0)
    var_map = np.var(stack.astype(np.float32), axis=0)
    mask = (var_map < var_thresh).astype(np.uint8)  # 1 where static
    mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=1)  # expand slightly
    return mask

if __name__ == "__main__":
    video_path = "input_videos/video_1.mp4"

    frames = load_frames(video_path, sample_rate=5)
    mask = create_temporal_mask(frames, var_thresh=12)

    aligned = align_frames_sift(frames, ignore_mask=mask)
    background = create_clean_background(aligned)

    cv2.imshow("Player-Free Court", background)
    cv2.waitKey(0)

    cv2.destroyAllWindows()