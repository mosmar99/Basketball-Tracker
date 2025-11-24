import os
import json
import requests

DETECTOR_URL = os.getenv("DETECTOR_URL", "http://localhost:8000/track")
ASSIGNER_URL = os.getenv("TEAM_ASSIGNER_URL", "http://localhost:8001/assign_teams")

def get_team_assignments_from_service(local_video_path: str, player_tracks):
    url = ASSIGNER_URL
    tracks_json_str = json.dumps(player_tracks)
    with open(local_video_path, "rb") as f:
        files = {
            "file": (local_video_path, f, "video/mp4"),
            "player_tracks_file": ("player_tracks.json", tracks_json_str.encode("utf-8"), "application/json")
        }
        r = requests.post(url, files=files)
    r.raise_for_status()
    data = r.json()
    return data["team_assignments"]

def get_tracks_from_service(local_video_path: str):
    url = DETECTOR_URL
    with open(local_video_path, "rb") as f:
        files = {"file": (local_video_path, f, "video/mp4")}
        r = requests.post(url, files=files)
    r.raise_for_status()
    data = r.json()
    return data["player_tracks"], data["ball_tracks"]

def deserialize_tracks(serialized):
    tracks = []
    for frame in serialized:
        frame_dict = {}
        for obj in frame:
            track_id = int(obj["track_id"])
            bbox = obj.get("bbox", [])
            frame_dict[track_id] = {"bbox": bbox}
        tracks.append(frame_dict)
    return tracks

def deserialize_team_assignments(serialized):
    out = []
    for frame in serialized:
        frame_dict = {}
        for entry in frame:
            pid = int(entry["player_id"])
            tid = int(entry["team_id"])
            frame_dict[pid] = tid
        out.append(frame_dict)
    return out