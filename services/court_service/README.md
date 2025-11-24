
# Build service
To build the docker container, from the root directory, run the command: `docker build -t court-service -f court_service/Dockerfile .`  
The service can then be launched from the root directory togehter with the other services using `docker-compose up -d`

## API Endpoints

### 1. `POST /stitch`

Creates a panoramic image of the basketball court by stitching together frames from an input video.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `video` | File | The basketball game video to be processed  in `.mp4` format. |

**Example Request (`curl`):**
```bash
curl -X POST \
  -F "video=@/path/to/your/video.mp4" \
  http://localhost:8002/stitch
```

**Example Success Response (200 OK):**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "panorama_uri": "s3://basketball-panorama/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg",
  "width": 3840,
  "height": 720,
  "device": "cuda"
}
```
---
### 2. `POST /warp_panorama`

Applies a perspective warp to an existing panorama image based on 4 user-defined points, creating a top-down view of the court.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `panorama_uri` | String | The S3 URI of the source panorama image (obtained from the `/stitch` endpoint). |
| `points_json_str` | String | A JSON string representing a list of 4 `[x, y]` source points from the panorama. The order should be top-left, top-right, bottom-right, bottom-left. |

**Example Request (`curl`):**
```bash
curl -X POST \
  -F "panorama_uri=s3://basketball-panorama/a1b2c3d4-e5f6-7890-1234-567890abcdef.jpg" \
  -F 'points_json_str=[[150,200],[1800,210],[1950,950],[50,940]]' \
  http://localhost:8002/warp_panorama
```

**Example Success Response (200 OK):**
```json
{
  "job_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
  "warped_image_uri": "s3://basketball-panorama-warp/b2c3d4e5-f6a7-8901-2345-67890abcdef1.jpg",
  "width": 2560,
  "height": 768,
  "device": "cuda"
}
```
---
### 3. `POST /homographyframe`

Calculates the homography matrix between a single image frame and a reference court image.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `frame` | File | The input image frame (e.g., a `.jpg` or `.png` file). |
| `reference` | File | The reference court image (e.g., a top-down view of a court). |

**Example Request (`curl`):**
```bash
curl -X POST \
  -F "frame=@/path/to/game_frame.jpg" \
  -F "reference=@/path/to/reference_court.jpg" \
  http://localhost:8002/homographyframe
```

**Example Success Response (200 OK):**
```json
{
  "success": true,
  "homography": [
    [1.23, -0.05, 150.7],
    [0.02, 1.19, 55.2],
    [0.0001, -0.0002, 1.0]
  ]
}
```
---
### 4. `POST /homographyvideo`

Calculates a homography matrix for each frame of an input video against a single reference court image.

**Request:** `multipart/form-data`

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `video` | File | The input video in `.mp4` format. |
| `reference` | File | The single reference court image. |

**Example Request (`curl`):**
```bash
curl -X POST \
  -F "video=@/path/to/your/video.mp4" \
  -F "reference=@/path/to/reference_court.jpg" \
  http://localhost:8002/homographyvideo
```

**Example Success Response (200 OK):**
```json
{
  "job_id": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
  "H": [
    [
      [1.23, -0.05, 150.7],
      [0.02, 1.19, 55.2],
      [0.0001, -0.0002, 1.0]
    ],
    null,
    [
      [1.25, -0.04, 152.1],
      [0.03, 1.20, 56.8],
      [0.0001, -0.0002, 1.0]
    ]
  ]
}
```
