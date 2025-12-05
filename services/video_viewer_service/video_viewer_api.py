from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from shared.storage import get_s3

BUCKET_RAW = "basketball-raw-videos"
BUCKET_PROCESSED = "basketball-processed"
BUCKET_FIGURES = "figures"

app = FastAPI(title="Video Viewer Service")

@app.get("/stats_image/{video_name}")
def serve_stats_image(video_name: str):
    s3 = get_s3()
    key = f"{video_name}.png"

    try:
        obj = s3.get_object(Bucket=BUCKET_FIGURES, Key=key)
        img_bytes = obj["Body"].read()
    except Exception:
        raise HTTPException(status_code=404, detail="Statistics image not found")

    return Response(content=img_bytes, media_type="image/png")

@app.get("/video/{bucket}/{video_name}")
def stream_s3(bucket:str, video_name: str):
    s3 = get_s3()
    key = f"{video_name}.mp4"

    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except Exception:
        raise HTTPException(status_code=404, detail="video not found")

    return StreamingResponse(obj["Body"], media_type="video/mp4")

@app.get("/video_processed/{video_name}")
async def stream_processed(request: Request, video_name: str):
    s3 = get_s3()
    key = f"{video_name}.mp4"

    try:
        head = s3.head_object(Bucket=BUCKET_PROCESSED, Key=key)
        file_size = head["ContentLength"]
    except Exception:
        raise HTTPException(status_code=404, detail="Processed video not found")

    range_header = request.headers.get("range")
    if range_header:
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        end = int(bytes_range[1] or (file_size - 1))
    else:
        start = 0
        end = file_size - 1

    chunk_size = end - start + 1

    stream_obj = s3.get_object(
        Bucket=BUCKET_PROCESSED,
        Key=key,
        Range=f"bytes={start}-{end}"
    )

    content = stream_obj["Body"].read()

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": "video/mp4",
    }

    return Response(content, status_code=206, headers=headers)

@app.get("/video_statistics/{video_name}")
def video_statistics(video_name: str):
    html = f"""
    <html>
    <body style="font-family: Arial; max-width: 1000px; margin: auto;">

        <h2>Raw Video: {video_name}</h2>
        <video width="100%" controls style="margin-bottom: 40px;">
            <source src="/video/basketball-raw-videos/{video_name}" type="video/mp4">
        </video>

        <h2>Processed Video: {video_name}</h2>
        <video width="100%" controls style="margin-bottom: 40px;">
            <source src="/video/basketball-processed/{video_name}" type="video/mp4">
        </video>

        <h2>Minimap View: {video_name}</h2>
        <video width="100%" controls style="margin-bottom: 40px;">
            <source src="/video/basketball-minimap/{video_name}" type="video/mp4">
        </video>
        
        <h2 style="text-decoration: underline;">Statistics</h2>

        <h3 style="margin-top: 20px;">Ball Possession Plot</h3>
        <img src="/stats_image/{video_name}"
             alt="Ball Possession Plot"
             style="width:100%; border:1px solid #ccc; margin-top:10px;"/>

        <h3 style="margin-top: 20px;">Court Control Plot</h3>
        <img src="/stats_image/{video_name}_mm"
             alt="Ball Possession Plot"
             style="width:100%; border:1px solid #ccc; margin-top:10px;"/>

    </body>
    </html>
    """
    return HTMLResponse(html)
