# Video Viewer Service
Build the Docker container:  
`docker build -t video-viewer-service -f video_viewer_service/Dockerfile .`  

Run with docker-compose:  
`docker-compose up -d`

---

## API Endpoints

### 1. `GET /stats_image/{video_name}`
Serves a statistics image (PNG) for a given video.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_name` | string | Base name of the video. Corresponding image key: `{video_name}.png` in S3 `figures` bucket. |

**Example Request (`curl`):**
```bash
curl http://localhost:8003/stats_image/game1
```

**Success Response (200 OK):** </br>
Returns raw PNG image (image/png). </br>

### 2. `GET /video/{bucket}/{video_name}`
Streams a video file (.mp4) from a specified S3 bucket.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `bucket` | string | S3 bucket name (basketball-raw-videos, basketball-processed, figures, etc.) |
|`video_name` | string | Base name of the video|

**Example Request (`curl`):**
```bash
curl http://localhost:8003/video/basketball-raw-videos/game1
```

**Success Response (200 OK):** </br>
Returns streaming video (video/mp4). </br>

### 3. `GET /video_processed/{video_name}`
Streams a processed video with support for HTTP Range Requests (for partial content / seeking).

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_name` | string | Base name of the processed video (.mp4) in basketball-processed bucket. |

### 4. `GET /video_statistics/{video_name}`
Returns an HTML page displaying:

- Raw video
- Processed video
- Minimap video
- Ball possession plot
- Court control plot
- Passes per team plot
- Interceptions per team plot

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `video_name` | string | Base name of the video.|

**Example Request (`curl`):**
```bash
curl http://localhost:8003/video_statistics/game1
```

**Success Response (200 OK):** </br>
Returns a fully formatted HTML page with embedded video players and statistics images. </br>