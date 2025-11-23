import os
import uuid
import cv2
import torch
import bentoml
import numpy as np
from PIL.Image import Image # Use standard PIL Image for type hinting

from processing.court_stitcher import CourtStitcher
from processing.inference import HomographyInference

from utils.video_io import load_frames
from utils.s3 import upload_to_s3

@bentoml.service(
    name="Homography",
    image=bentoml.images.Image(python_version="3.11").python_packages("torch", "transformers"),
)
class Homography:
    def __init__(self):
        self.DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
        self.stitcher = CourtStitcher(self.DEVICE)
        self.homography = HomographyInference(self.DEVICE)

    @bentoml.api(route="/stitch")
    def stitch_panorama(self, video):
        job_id = str(uuid.uuid4())
        tmp_video = f"/tmp/{job_id}.mp4"
        tmp_output_img = f"/tmp/{job_id}.jpg"

        video.save(tmp_video)
        frames = load_frames(tmp_video, sample_rate=3)

        panorama = self.stitcher.align_and_stitch(frames)

        cv2.imwrite(tmp_output_img, panorama)

        s3_uri = upload_to_s3(tmp_output_img, "panoramas", f"{job_id}.jpg")

        h, w = panorama.shape[:2]

        os.remove(tmp_video)
        os.remove(tmp_output_img)

        return {
            "job_id": job_id,
            "panorama_uri": s3_uri,
            "width": w,
            "height": h,
            "device": self.DEVICE
        }

    @bentoml.api(route="/homography")
    def estimate_homography(self, frame: Image, reference: Image):
        frame_np = np.asarray(frame)
        ref_np = np.asarray(reference)

        H = self.homography.estimate_court_homography(frame_np, ref_np)

        if H is None:
            return {"success": False, "error": "Not enough matches"}

        return {
            "success": True,
            "homography": H.tolist()
        }
