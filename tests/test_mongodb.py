import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
port = os.getenv("MONGODB_PORT", "27017")
user = os.getenv("MONGODB_USER", "root")
password = os.getenv("MONGODB_PASS", "password")

MONGODB_URI = f"mongodb://{user}:{password}@localhost:{port}/"
print("Connecting to:", MONGODB_URI)

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

try:
    result = client.admin.command("ping")
    print("Successfully connected to MongoDB!")
    print(result)
except Exception as e:
    print("MongoDB connection failed!")
    print("Error:", e)
