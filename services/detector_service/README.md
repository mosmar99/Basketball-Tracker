# Tracking Service
To build the Docker container, from the root directory, run the command: `docker build -t tracking-service -f tracking_service/Dockerfile .`  
The service can then be launched together with the other services using `docker-compose up -d`

## API Endpoints

---

### 1. `POST /track`

Runs player and ball tracking on an uploaded video.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `file` | File | The input game video in `.mp4` format. |

**Example Request (`curl`):**
```bash
curl -X POST \
  -F "file=@/path/to/your/video.mp4" \
  http://localhost:8001/track
```

**Example Success Response (200 OK):**

```json
{
  "player_tracks": [
    [
      {
        "track_id": 1,
        "bbox": [100.5, 220.0, 160.2, 330.8]
      },
      {
        "track_id": 2,
        "bbox": [300.1, 240.8, 360.2, 350.7]
      }
    ],
    [
      {
        "track_id": 1,
        "bbox": [102.2, 221.4, 161.1, 332.9]
      }
    ]
  ],
  "ball_tracks": [
    [
      {
        "track_id": 1,
        "bbox": [500.4, 200.2, 520.1, 220.0]
      }
    ]
  ]
}
```

**Description:**
- Loads production player and ball tracking models.

- Saves the uploaded video temporarily.

- Extracts video frames and runs object tracking.

- Produces per-frame bounding boxes for players and the ball.

- Ball tracks are cleaned and interpolated to remove incorrect detections.