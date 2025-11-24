import cv2
import torch
import numpy as np
from tqdm import tqdm

def warp_to_cylinder(frame, f):
    h, w = frame.shape[:2]
    jj, ii = np.meshgrid(np.arange(w), np.arange(h))
    ii_c = ii - h / 2
    jj_c = jj - w / 2
    theta = jj_c / f
    h_prime = ii_c / f
    x_3d = np.sin(theta)
    y_3d = h_prime
    z_3d = np.cos(theta)
    x_2d = f * x_3d / z_3d
    y_2d = f * y_3d / z_3d
    map_x = (x_2d + w / 2).astype(np.float32)
    map_y = (y_2d + h / 2).astype(np.float32)
    warped_img = cv2.remap(frame, map_x, map_y, cv2.INTER_LINEAR)
    return warped_img

class CourtStitcher:
    def __init__(self, device):
        self.device = device

    def align_frames_sift_cylindrical_homography(self, frames, ignore_masks=None, border=50):
        sift = cv2.SIFT_create()
        h, w = frames[0].shape[:2]

        focal_length = w * 1.6
        cylindrical_frames = [warp_to_cylinder(f, focal_length) for f in tqdm(frames, desc="[INFO] Warping frames to cylinder")]

        # --- Warp masks to cylindrical space if provided ---
        cylindrical_masks = None
        if ignore_masks is not None:
            cylindrical_masks = [warp_to_cylinder(m, focal_length) for m in ignore_masks]
            valid_masks = [(1 - m.astype(np.uint8)) for m in cylindrical_masks]
        else:
            valid_masks = [np.ones_like(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), dtype=np.uint8) for f in frames]

        prev_gray = cv2.cvtColor(cylindrical_frames[0], cv2.COLOR_BGR2GRAY)
        prev_valid_mask = valid_masks[0]
        kp_prev, des_prev = sift.detectAndCompute(prev_gray, prev_valid_mask)

        M_matrices = [np.eye(3)]  # transformations from each frame to the global reference (frame 0)

        # --- Estimate homographies ---
        for i in tqdm(range(1, len(cylindrical_frames)), desc="[INFO] Estimating homographies"):
            gray = cv2.cvtColor(cylindrical_frames[i], cv2.COLOR_BGR2GRAY)
            valid_mask = valid_masks[i]
            kp, des = sift.detectAndCompute(gray, valid_mask)

            M_curr = M_matrices[-1].copy()  # fallback

            if des is not None and des_prev is not None:
                matcher = cv2.BFMatcher()
                matches = matcher.knnMatch(des, des_prev, k=2)
                good = [m for m, n in matches if m.distance < 0.75 * n.distance]

                if len(good) > 20:
                    src_pts = np.float32([kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp_prev[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                    H_curr_to_prev, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                    if H_curr_to_prev is not None:
                        M_curr = M_matrices[-1] @ H_curr_to_prev

            M_matrices.append(M_curr)
            kp_prev, des_prev = kp, des

        # --- Determine panorama bounds ---
        corners = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32).reshape(-1, 1, 2)
        all_corners = np.concatenate([cv2.perspectiveTransform(corners, M) for M in M_matrices], axis=0)
        [xmin, ymin] = np.int32(all_corners.min(axis=0).ravel() - border)
        [xmax, ymax] = np.int32(all_corners.max(axis=0).ravel() + border)
        tx, ty = -xmin, -ymin
        panorama_size = (xmax - xmin, ymax - ymin)

        # --- Warp all frames & masks into global panorama canvas ---
        aligned_frames = []
        aligned_masks = [] if cylindrical_masks is not None else None
        translation_matrix = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]])

        for i, frame in enumerate(tqdm(cylindrical_frames, desc="[INFO] Warping to global panorama")):
            M_final = translation_matrix @ M_matrices[i]
            warped_frame = cv2.warpPerspective(frame, M_final, panorama_size)
            aligned_frames.append(warped_frame)

            if cylindrical_masks is not None:
                warped_mask = cv2.warpPerspective(cylindrical_masks[i], M_final, panorama_size)
                aligned_masks.append((warped_mask > 0).astype(np.uint8))

        return aligned_frames, aligned_masks, panorama_size, M_matrices

    def create_clean_background(self, frames):
        h, w, c = frames[0].shape 
        background = np.zeros((h, w, c), dtype=np.uint8)

        # Process one row at a time (OOM)
        for y in tqdm(range(h), desc="[INFO] Calculating median row-by-row"):
            row_stack = np.array([frame[y] for frame in frames])
            
            for x in range(w):
                pixel_column = row_stack[:, x, :]
                mask = np.any(pixel_column > 0, axis=1)
                valid_pixels = pixel_column[mask]
                
                if valid_pixels.shape[0] > 0:
                    median_pixel = np.median(valid_pixels, axis=0).astype(np.uint8)
                    background[y, x] = median_pixel
                    
        return background

    def create_clean_background_torch(self, frames, chunk_size=64):
        import torch
        stack = np.stack(frames).astype(np.float32) / 255.0  # (N, H, W, 3)
        N, H, W, C = stack.shape

        background = np.zeros((H, W, C), dtype=np.uint8)

        for y0 in tqdm(range(0, H, chunk_size), desc="[INFO] Background median (GPU chunks)"):
            y1 = min(y0 + chunk_size, H)
            chunk = torch.from_numpy(stack[:, y0:y1]).permute(0, 3, 1, 2).to(self.device)  # (N,3,h,W)
            mask = (chunk > 0).any(dim=1, keepdim=True)

            # Replace black pixels with NaN
            chunk_masked = chunk.clone()
            chunk_masked[~mask.expand_as(chunk_masked)] = float('nan')

            # Compute median ignoring NaNs
            isnan = torch.isnan(chunk_masked)
            chunk_masked[isnan] = 1e6
            chunk_sorted, _ = torch.sort(chunk_masked, dim=0)
            valid_counts = (~isnan).sum(dim=0)
            median_idx = (valid_counts.float() / 2).floor().long().clamp(min=0)
            # Gather median along frame dimension
            idx = median_idx.unsqueeze(0).expand_as(chunk_sorted[:1])  # (1, 3, h, W)
            chunk_median = torch.gather(chunk_sorted, 0, idx).squeeze(0)  # (3, h, W)

            chunk_median = (chunk_median * 255).clamp(0, 255).byte().permute(1, 2, 0).cpu().numpy()
            background[y0:y1] = chunk_median

            del chunk, mask, chunk_masked, chunk_sorted, chunk_median
            torch.cuda.empty_cache()

        return background

    def create_temporal_mask(self, frames, var_thresh=2.0):
        stack = np.stack([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames], axis=0)
        var_map = np.var(stack.astype(np.float32), axis=0)
        mask = (var_map < var_thresh).astype(np.uint8)
        mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=3)
        return mask

    def draw_bbox_mask(self, frame, bbox, color):
        x1, y1, x2, y2 = map(int, bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=cv2.FILLED)
        
        return frame

    def mask_from_track(self, track, frame):
        height, width = frame.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)

        for _, val in track.items():
            bbox = val.get("bbox", None)
            if bbox is not None:
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(mask, (x1, y1), (x2, y2), 1, thickness=cv2.FILLED)

        return mask
    
    def mask_aligned_frames(self, aligned_frames, aligned_masks):
        aligned_masked = []
        for frame, mask in zip(aligned_frames, aligned_masks):
            masked = frame.copy()
            masked[mask > 0] = 0
            aligned_masked.append(masked)
        return aligned_masked
    
    def align_and_stitch(self, frames):
        temporal_mask = self.create_temporal_mask(frames, var_thresh=12)
        masks = [temporal_mask for _ in range(len(frames))]
        
        aligned, aligned_masks, _, _ = self.align_frames_sift_cylindrical_homography(frames, ignore_masks=masks)

        aligned_masked = self.mask_aligned_frames(aligned, aligned_masks)
        background = self.create_clean_background_torch(aligned_masked)

        return background

if __name__ == "__main__":
    from utils import load_frames
    video_path = "../input_videos/video_1.mp4"
    frames = load_frames(video_path, sample_rate=5)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    cs = CourtStitcher(device)
    background = cs.align_and_stitch(frames)
    
    cv2.imshow("Player-Free Court (Cylindrical Projection - Homography)", background)
    cv2.imwrite("imgs/player_free_background_homography.jpg", background)
    print("[INFO] Saved background image to player_free_background_homography.jpg")
    cv2.waitKey(0)
    cv2.destroyAllWindows()