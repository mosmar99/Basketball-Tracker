import os
import uuid
import cv2
import torch
import numpy as np
import json
from fastapi import FastAPI, UploadFile, File, Form
import uvicorn

from .processing.court_stitcher import CourtStitcher
from .processing.inference import HomographyInference
from .processing.warp_panorama import warp_image

from .utils.video_io import load_frames
from shared.storage import s3_upload, download_to_temp

app = FastAPI(title="Homography Service")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
stitcher = CourtStitcher(DEVICE)
homography = HomographyInference(DEVICE)

@app.post("/stitch")
async def stitch_panorama_ep(video: UploadFile = File(...)):
    # job_id = str(uuid.uuid4())
    filename_img = f"{video.filename.split('.')[0]}.jpg"
    tmp_video = f"/tmp/{video.filename}"
    tmp_output_img = f"/tmp/{filename_img}"

    with open(tmp_video, "wb") as f:
        f.write(await video.read())

    frames = load_frames(tmp_video, sample_rate=3)

    panorama = stitcher.align_and_stitch(frames)
    cv2.imwrite(tmp_output_img, panorama)

    s3_uri = s3_upload(tmp_output_img, filename_img, BUCKET_NAME="basketball-panorama")

    h, w = panorama.shape[:2]

    os.remove(tmp_video)

    return {
        "job_id": filename_img,
        "panorama_uri": s3_uri,
        "width": w,
        "height": h,
        "device": DEVICE,
    }

@app.post("/warp_panorama")
async def warp_panorama_ep(panorama_uri: str = Form(...), points_json_str: str = Form(...)):
    # job_id = str(uuid.uuid4())
    points_data = json.loads(points_json_str)

    source_points = np.array(points_data, dtype=np.float32)
    if source_points.shape != (4, 2):
        return {"success": False, "error": f"Invalid points format, should be (4,2)"}

    bucket, key = panorama_uri.replace("s3://", "").split("/", 1)
    local_panorama_path = download_to_temp(key, bucket)

    panorama_img = cv2.imread(local_panorama_path)

    warped_img = warp_image(panorama_img, source_points)
    
    tmp_warped_path = f"/tmp/{key}"
    cv2.imwrite(tmp_warped_path, warped_img)
    warped_s3_uri = s3_upload(tmp_warped_path, key, BUCKET_NAME="basketball-panorama-warp")

    h, w = warped_img.shape[:2]

    os.remove(local_panorama_path)
    os.remove(tmp_warped_path)

    return {
        "job_id": key,
        "warped_image_uri": warped_s3_uri,
        "width": w,
        "height": h,
        "device": DEVICE,
    }

@app.post("/homographyframe")
async def estimate_homography_ep(frame: UploadFile = File(...), reference: UploadFile = File(...)):
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
async def stitch_panorama_ep(video: UploadFile = File(...), reference: UploadFile = Form(...)):
    job_id = str(uuid.uuid4())
    tmp_video = f"/tmp/{job_id}.mp4"

    ref_contents = await reference.read()
    ref_nparr = np.frombuffer(ref_contents, np.uint8)
    ref_bgr = cv2.imdecode(ref_nparr, cv2.IMREAD_COLOR)

    with open(tmp_video, "wb") as f:
        f.write(await video.read())

    frames = load_frames(tmp_video, sample_rate=1)

    H = []
    for frame in frames:
        H_matrix = homography.estimate_court_homography(frame, ref_bgr)
        
        if H_matrix is not None:
            H.append(H_matrix.tolist())
        else:
            H.append(None)

    os.remove(tmp_video)

    return {
        "job_id": job_id,
        "H": H,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)