import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_HOST = os.getenv("MONGODB_HOST", "mongodb")
MONGO_PORT = os.getenv("MONGODB_PORT", "27017")
MONGO_USER = os.getenv("MONGODB_USER", "root")
MONGO_PASS = os.getenv("MONGODB_PASS", "password")

MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"

client = MongoClient(MONGO_URI)
db = client["basketball"]
possessions = db["ball_possession"]
control = db["minimap"]

def save_ball_possession(video_id, ball_team_possessions, fps=30):
    time = datetime.now(ZoneInfo("Europe/Stockholm"))

    doc = {
        "video_id": video_id,
        "created_at": time,
        "total_frames": len(ball_team_possessions),
        "fps": fps,
        "ball_possession": ball_team_possessions,
    }

    possessions.update_one(
        {"video_id": video_id},
        {"$set": doc},
        upsert=True,
    )

def save_control_stats(video_id, control_stats, fps=30):
    time = datetime.now(ZoneInfo("Europe/Stockholm"))
    cleaned_stats = [{str(k): v for k, v in frame.items()} for frame in control_stats] # Sting keys required
    doc = {
        "video_id": video_id,
        "created_at": time,
        "total_frames": len(control_stats),
        "fps": fps,
        "control_stats": cleaned_stats,
    }

    control.update_one(
        {"video_id": video_id},
        {"$set": doc},
        upsert=True,
    )
