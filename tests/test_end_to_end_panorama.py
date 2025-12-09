from shared import upload_video, download_to_temp, list_bucket_contents
import requests
from services.ui_service import config
import os
import json
import numpy as np
import cv2

VIDEO = config.VIDEO

def t_stitch(video_path):
    try:
        basename = os.path.basename(video_path)
        upload_video(video_path, basename, config.BUCKET_RAW)
        
        with open(video_path, "rb") as f:
            resp = requests.post(config.DEFAULT_STITCH, files={"video": (basename, f, "video/mp4")})
        
        if resp.status_code != 200:
            assert(False)
            
        data = resp.json()

        assert(True)
        return data  
    except Exception as e:
        assert(False)

def t_wrap(panorama_uri, court_name):
    bucket, key = panorama_uri.replace("s3://", "").split("/", 1)
    local_panorama_path = download_to_temp(key, bucket)
    image = cv2.imread(local_panorama_path)
    h, w = image.shape[:2]

    points = np.array([
        [0, 0],      # top-left
        [w, 0],      # top-right
        [w, h],      # bottom-right
        [0, h]       # bottom-left
    ], dtype=np.float32)

    try:
        payload = {
            "panorama_uri": panorama_uri,
            "points_json_str": json.dumps(points.tolist()),
            "court_name": court_name.strip()
        }
        resp = requests.post(config.DEFAULT_WARP, data=payload)
        
        assert(resp.status_code == 200)
    except Exception as e:
        assert(False)

def test_main():
    local = "tests/"
    r = t_stitch(local+VIDEO)
    t_wrap(r['panorama_uri'], VIDEO.replace('.mp4','') + '.jpg')

    contents = []
    contents.append(list_bucket_contents(config.BUCKET_COURTS))
    contents.append(list_bucket_contents(config.BUCKET_COURT_P))
    print(contents)
    all_successful = False
    for content in contents:
        if VIDEO.replace('.mp4','') + '.jpg' in content:
            all_successful = True

    assert(all_successful)

if __name__ == "__main__":
    test_main()