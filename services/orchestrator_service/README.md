# Processing Service
To build the Docker container, from the root directory, run the command:  
`docker build -t processing-service -f processing_service/Dockerfile .`  
The service can then be launched together with the other services using:  
`docker-compose up -d`

## API Endpoints

---

### 1. `POST /process`

Runs the full analytics pipeline on a game video, including tracking, team assignment, ball possession, passes/interceptions, homographies, drawing full overlays, generating a minimap, and uploading processed outputs.

**Request:** `application/x-www-form-urlencoded`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `video_name` | String | Base name of the video stored in the raw-videos bucket (e.g., `game1` → loads `game1.mp4`). |
| `reference_court` | String | Key of the warped panorama in the panorama-warp bucket. |

**Example Request (`curl`):**
```bash
curl -X POST \
  -d "video_name=game1" \
  -d "reference_court=game1_warped.jpg" \
  http://localhost:8000/process
```

**Example Success Response (200 OK):**

```json
{
  "status": "completed",
  "ball_tp": [1, 1, 2, 2, 1],
  "vid_name": "game1",
  "control_stats": { "1": 52.3, "2": 47.7 },
  "pi_stats": {
    "1": { "passes": 2, "interceptions": 6 },
    "2": { "passes": 4, "interceptions": 4 }
  },
  "team_colors": {
    "1": [220, 20, 60],
    "2": [30, 144, 255]
  }
}
```

## Description

### 1. Download Inputs
- Video (`.mp4`) from **basketball-raw-videos**
- Warped court panorama from **basketball-panorama-warp**
- Local court image (base court)

---

### 2. Tracking
Queries the **tracking microservice**.  
Returns:
- `player_tracks`
- `ball_tracks`

---

### 3. Team Assignment
Queries the **team-assignment microservice**.  
Returns:
- **`team_assignments`** — list indexed by frame  
  - Example lookup:  
    ```python
    team_current_player = team_assignments[frame_idx].get(player_id)
    ```
- **`team_colors`** — JSON object:  
  ```json
  { "1": [b, g, r], "2": [b, g, r] }
  ```

### 4. Ball Possession / Passes / Interceptions
Using BallAcquisitionSensor:

- Detects ball possession events
- Converts them into team-level possession sequences
- Computes pass & interception statistics
- Computes control statistics (ball possession share per team)

### 5. Homographies
Loads per-frame homographies from the homography service.

### 6. Rendering
Adds overlays:
- Player tracks
- Ball trajectory
- Team coloring
- Ball-possession highlights

Generates two videos:
- Full broadcast annotated output video
- Minimap (top-down) video


### 7. Save + Upload
Outputs are:
- Saved locally
- Repackaged using ffmpeg for HTML compatibility

Uploaded to:
- basketball-processed
- basketball-minimap

### 8. Save Stats
Writes ball-possession and control statistics to MongoDB.