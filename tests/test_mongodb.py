import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_HOST = os.getenv("MONGODB_HOST", "127.0.0.1")
MONGODB_PORT = os.getenv("MONGODB_PORT", "27017")

uri = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/"
client = MongoClient(uri)

try:
    client.admin.command("ping")
    print(f"Connected to MongoDB at {uri}")
except Exception as e:
    print("Connection failed:", e)
