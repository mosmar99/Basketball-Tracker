import os
import uuid
import cv2
import torch
import numpy as np
from fastapi import FastAPI, UploadFile, File
from PIL import Image

from processing.court_stitcher import CourtStitcher
from processing.inference import HomographyInference

from utils.video_io import load_frames
from utils.s3 import upload_to_s3


app = FastAPI(title="Homography Service")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
stitcher = CourtStitcher(DEVICE)
homography = HomographyInference(DEVICE)

@app.post("/stitch")
async def stitch_panorama(video: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    tmp_video = f"/tmp/{job_id}.mp4"
    tmp_output_img = f"/tmp/{job_id}.jpg"

    with open(tmp_video, "wb") as f:
        f.write(await video.read())

    frames = load_frames(tmp_video, sample_rate=3)

    panorama = stitcher.align_and_stitch(frames)
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
        "device": DEVICE,
    }

@app.post("/homography")
async def estimate_homography(frame: UploadFile = File(...), reference: UploadFile = File(...)):
    frame_img = Image.open(frame.file).convert("RGB")
    ref_img = Image.open(reference.file).convert("RGB")

    frame_np = np.asarray(frame_img)
    ref_np = np.asarray(ref_img)

    H = homography.estimate_court_homography(frame_np, ref_np)

    if H is None:
        return {"success": False, "error": "Not enough matches"}

    return {
        "success": True,
        "homography": H.tolist()
    }