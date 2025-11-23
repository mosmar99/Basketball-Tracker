import os
import uuid
import cv2
import torch
import numpy as np
from fastapi import FastAPI, UploadFile, File
import uvicorn

from .processing.court_stitcher import CourtStitcher
from .processing.inference import HomographyInference

from .utils.video_io import load_frames
from shared.storage import upload_video, upload_panorama, download_to_temp


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

    s3_uri = upload_panorama(tmp_output_img, f"{job_id}.jpg")

    h, w = panorama.shape[:2]

    os.remove(tmp_video)

    return {
        "job_id": job_id,
        "panorama_uri": s3_uri,
        "width": w,
        "height": h,
        "device": DEVICE,
    }

@app.post("/homographyframe")
async def estimate_homography(frame: UploadFile = File(...), reference: UploadFile = File(...)):
    frame_contents = await frame.read()
    frame_nparr = np.frombuffer(frame_contents, np.uint8)
    frame_bgr = cv2.imdecode(frame_nparr, cv2.IMREAD_COLOR)

    ref_contents = await reference.read()
    ref_nparr = np.frombuffer(ref_contents, np.uint8)
    ref_bgr = cv2.imdecode(ref_nparr, cv2.IMREAD_COLOR)

    H = homography.estimate_court_homography(frame_bgr, ref_bgr)

    if H is None:
        return {"success": False, "error": "Not enough matches"}

    return {
        "success": True,
        "homography": H.tolist()
    }

@app.post("/homographyvideo")
async def stitch_panorama(video: UploadFile = File(...), reference: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    tmp_video = f"/tmp/{job_id}.mp4"
    tmp_output_img = f"/tmp/{job_id}.jpg"

    ref_contents = await reference.read()
    ref_nparr = np.frombuffer(ref_contents, np.uint8)
    ref_bgr = cv2.imdecode(ref_nparr, cv2.IMREAD_COLOR)

    with open(tmp_video, "wb") as f:
        f.write(await video.read())

    frames = load_frames(tmp_video, sample_rate=1)

    H = [homography.estimate_court_homography(frame, ref_bgr).tolist() for frame in frames]

    os.remove(tmp_video)

    return {
        "job_id": job_id,
        "H": H,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)