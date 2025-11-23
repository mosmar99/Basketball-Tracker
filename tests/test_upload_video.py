from shared.storage import upload_video

BUCKET_RAW = "basketball-raw-videos"
BUCKET_PROCESSED = "basketball-processed"
BUCKET_MODELS = "basketball-models"

def test_upload_video():
    vid_name = "video_2"
    local_path = f"input_videos/{vid_name}.mp4"
    key = f"{vid_name}.mp4"
    uri = upload_video(local_path, key, BUCKET_NAME=BUCKET_RAW)
    print("Uploaded to:", uri)

if __name__ == "__main__":
    test_upload_video()