import requests

resp = requests.post(
    "http://localhost:8002/process",
    params={"video_name": "video_1"}
)