from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import uvicorn
import tempfile
from pathlib import Path

from tracking import PlayerTracker, BallTracker, get_production_model_path
from utils import read_video

def serialize_tracks(tracks):
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

app = FastAPI()

model_path = get_production_model_path()

@app.post("/track")
async def track_video(file: UploadFile = File(...)):
    player_tracker = PlayerTracker(model_path=model_path)
    ball_tracker = BallTracker(model_path=model_path)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / file.filename
        with tmp_path.open("wb") as f:
            f.write(await file.read())

        frames = read_video(str(tmp_path))

        player_tracks = player_tracker.get_object_tracks(
            frames,
        )
        ball_tracks = ball_tracker.get_object_tracks(
            frames,
        )

        ball_tracks = ball_tracker.remove_incorrect_detections(ball_tracks)
        ball_tracks = ball_tracker.interp_ball_pos(ball_tracks)

    payload = {
        "player_tracks": serialize_tracks(player_tracks),
        "ball_tracks": serialize_tracks(ball_tracks),
    }
    safe_payload = jsonable_encoder(payload)
    return JSONResponse(content=safe_payload)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
