from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn
import tempfile
from pathlib import Path
import json

import sys
sys.path.append("../")

from utils import read_video
from team_assigner import TeamAssigner


app = FastAPI()


def serialize_team_assignments(assignments):
    out = []
    for frame in assignments:
        frame_list = []
        for pid, tid in frame.items():
            frame_list.append({
                "player_id": int(pid),
                "team_id": int(tid),
            })
        out.append(frame_list)
    return out


@app.post("/assign_teams")
async def assign_teams(
    file: UploadFile = File(...),
    player_tracks_file: UploadFile = File(...,
        description="Deserialized Python-style tracks as JSON")
):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save video
        tmp_video_path = Path(tmpdir) / file.filename
        with tmp_video_path.open("wb") as f:
            f.write(await file.read())

        # Save + load player_tracks JSON
        tmp_tracks_path = Path(tmpdir) / player_tracks_file.filename
        with tmp_tracks_path.open("wb") as f:
            f.write(await player_tracks_file.read())

        with tmp_tracks_path.open("r") as f:
            player_tracks = json.load(f)

    # Read video frames
    frames = read_video(str(tmp_video_path))

    # Run team assigner
    team_assigner = TeamAssigner(
        team_A="WHITE shirt",
        team_B="DARK BLUE shirt"
    )

    team_assignments = team_assigner.get_player_teams_over_frames(
        vid_frames=frames,
        player_tracks=player_tracks,
        read_from_stub=False,
        stub_path="stubs/player_assignment_stubs.pkl",
    )

    # Serialize
    payload = {
        "team_assignments": serialize_team_assignments(team_assignments)
    }

    safe = jsonable_encoder(payload)
    return JSONResponse(content=safe)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
