from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from shared.storage import get_s3

BUCKET_RAW = "basketball-raw-videos"
BUCKET_PROCESSED = "basketball-processed"

app = FastAPI(title="Video Viewer Service")


@app.get("/video_raw/{video_name}")
def stream_raw(video_name: str):
    s3 = get_s3()
    key = f"{video_name}.mp4"

    try:
        obj = s3.get_object(Bucket=BUCKET_RAW, Key=key)
    except Exception:
        raise HTTPException(status_code=404, detail="Raw video not found")

    return StreamingResponse(obj["Body"], media_type="video/mp4")


from fastapi import FastAPI, HTTPException, Response, Request

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
        # Example "bytes=0-"
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        end = int(bytes_range[1] or (file_size - 1))
    else:
        # No range header → browser still needs full file with correct metadata
        start = 0
        end = file_size - 1

    chunk_size = end - start + 1

    # Request only the needed bytes from MinIO
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

    # Status code 206 = Partial Content → REQUIRED for browser playback
    return Response(content, status_code=206, headers=headers)


@app.get("/video_statistics/{video_name}")
def video_statistics(video_name: str):
    html = f"""
    <html>
    <body style="font-family: Arial; max-width: 1000px; margin: auto;">

        <h2>Raw Video: {video_name}</h2>
        <video width="100%" controls style="margin-bottom: 40px;">
            <source src="/video_raw/{video_name}" type="video/mp4">
        </video>

        <h2>Processed Video: {video_name}</h2>
        <video width="100%" controls style="margin-bottom: 40px;">
            <source src="/video_processed/{video_name}" type="video/mp4">
        </video>

        <h2>Statistics</h2>
        <p>(Coming soon.)</p>

    </body>
    </html>
    """
    return HTMLResponse(html)
