import os
from pymongo import MongoClient

MONGODB_HOST = os.getenv("MONGODB_HOST", "127.0.0.1")
MONGODB_PORT = os.getenv("MONGODB_PORT", "27017")
uri = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/"

client = MongoClient(uri)

db = client["basketball_tracker"]
frames = db["frames"]
videos = db["videos"]

def save_video_metadata(video_id: str, video_name: str, fps: int, total_frames: int):
    videos.insert_one({
        "_id": video_id,
        "video_name": video_name,
        "fps": fps,
        "total_frames": total_frames
    })

def save_possession_frames(video_id: str, teamA_series, teamB_series):
    docs = []
    for i in range(len(teamA_series)):
        docs.append({
            "video_id": video_id,
            "frame": i,
            "possession": {
                "Team_A": teamA_series[i],
                "Team_B": teamB_series[i]
            }
        })
    if docs:
        frames.insert_many(docs)
