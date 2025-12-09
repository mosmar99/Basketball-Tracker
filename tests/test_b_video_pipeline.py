from shared.storage import upload_video
import os
from services.ui_service import config
from pathlib import Path
import requests

VIDEO_NAME = "s"
COURT = "video_1.jpg"

def t_upload_video(video_name = "tests/s.mp4"):

    local_path = Path(__file__).parent / video_name
    basename = os.path.basename(local_path)

    localpath = video_name

    upload_video(localpath, basename, config.BUCKET_RAW)
    print("Successfully, uploaded video to miniobucket")

def t_process(video_name, court_name):
    try:
        resp = requests.post(config.API_PROCESS, params={
            "video_name": video_name, 
            "reference_court": court_name
        })
    except:
        print(f"Failed to process video via {config.API_PROCESS}, backend unreachable")

    if resp.status_code != 200:
        print(f"Failed to process video via {config.API_PROCESS}, status: {resp.status_code}")

    print(f"Successfully, processed video via: {config.API_PROCESS}")
    return resp.json()


def test_main():
    local = "tests/"
    filetype = ".mp4"
    video_name = VIDEO_NAME
    court = COURT
    t_upload_video(local+video_name+filetype)
    r = t_process(video_name, court)

if __name__ == "__main__":
    test_main()