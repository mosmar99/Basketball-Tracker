# Team Assigner Service
Build the Docker container:  
`docker build -t team-assigner-service -f team_assigner_service/Dockerfile .`  

Run with docker-compose:  
`docker-compose up -d`

---

## API Endpoints

### 1. `POST /assign_teams`
Assigns players to teams for each frame of a basketball video using precomputed player tracks.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `file` | File | The input game video in `.mp4` format. |
| `player_tracks_file` | File | JSON file containing deserialized player tracks (from tracking service). |

**Example Request (`curl`):**
```bash
curl -X POST \
  -F "file=@/path/to/game.mp4" \
  -F "player_tracks_file=@/path/to/player_tracks.json" \
  http://localhost:8002/assign_teams
```

**Example Success Response (200 OK):**
```json
{
  "team_assignments": [
    [
      { "player_id": 1, "team_id": 1 },
      { "player_id": 2, "team_id": 2 }
    ],
    [
      { "player_id": 1, "team_id": 1 },
      { "player_id": 2, "team_id": 2 }
    ]
  ],
  "team_colors": {
    "1": [220, 20, 60],
    "2": [30, 144, 255]
  }
}
```

**Description**
Loads the uploaded video and player tracks JSON.

Reads frames from the video.

Uses the TeamAssigner service to assign each player to a team for every frame.

Returns:

- team_assignments: list of frame-indexed player-team mappings.

- Example usage: team_current_player = team_assignments[frame_idx].get(player_id)

- team_colors: mapping of team IDs to RGB colors.