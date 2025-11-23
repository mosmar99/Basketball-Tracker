from shared.storage import delete_video

def test_delete_video():
    key = "videos/video_1.mp4"
    uri = delete_video(key, BUCKET_NAME="basketball")
    print("Content at:", uri, "has been deleted.")

if __name__ == "__main__":
    test_delete_video()