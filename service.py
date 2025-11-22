from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn
import tempfile
from pathlib import Path

from tracking import PlayerTracker 
from tracking import BallTracker 
from tracking import get_production_model_path
    
import sys
sys.path.append("../")
from utils import read_video

app = FastAPI()

model_path = get_production_model_path()
player_tracker = PlayerTracker(model_path=model_path)
ball_tracker = BallTracker(model_path=model_path)

def serialize_tracks(tracks):
    """
    Convert tracks (list of dicts) into a JSON-serializable form:
    - frame-wise list of objects
    - each obj: {"track_id": int, "bbox": [float, float, float, float]}
    """
    out = []
    for frame in tracks:
        frame_objs = []
        for track_id, info in frame.items():
            # track_id might be numpy.int64
            track_id_int = int(track_id)
            bbox = info.get("bbox", [])
            # bbox elements might be numpy types
            bbox_list = [float(x) for x in bbox]
            frame_objs.append(
                {
                    "track_id": track_id_int,
                    "bbox": bbox_list,
                }
            )
        out.append(frame_objs)
    return out


@app.post("/track")
async def track_video(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / file.filename
        with tmp_path.open("wb") as f:
            f.write(await file.read())

        frames = read_video(str(tmp_path))

        player_tracks = player_tracker.get_object_tracks(
            frames,
            read_from_stub=False,
            stub_path="stubs/player_track_stubs.pkl",
        )
        ball_tracks = ball_tracker.get_object_tracks(
            frames,
            read_from_stub=False,
            stub_path="stubs/ball_track_stubs.pkl",
        )

    payload = {
        "player_tracks": serialize_tracks(player_tracks),
        "ball_tracks": serialize_tracks(ball_tracks),
    }
    safe_payload = jsonable_encoder(payload)
    return JSONResponse(content=safe_payload)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
