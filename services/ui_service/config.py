import os

# Defaults
LOCAL_HOST = "127.0.0.1"
DEFAULT_PROCESS = f"http://{LOCAL_HOST}:8000/process"
DEFAULT_STITCH  = f"http://{LOCAL_HOST}:8003/stitch"       # Local uses port 8003
DEFAULT_WARP    = f"http://{LOCAL_HOST}:8003/warp_panorama" # Local uses port 8003
DEFAULT_VIEWER  = f"http://{LOCAL_HOST}:8004"               # Local uses port 8004

# Load from env
API_PROCESS = os.getenv("API_URL_PROCESS", DEFAULT_PROCESS)
API_STITCH  = os.getenv("API_URL_STITCH", DEFAULT_STITCH)
API_WARP    = os.getenv("API_URL_WARP", DEFAULT_WARP)
VIEWER_BASE = os.getenv("API_URL_VIEWER", DEFAULT_VIEWER)

# Buckets
BUCKET_RAW = "basketball-raw-videos"
BUCKET_PROCESSED = "basketball-processed"
BUCKET_MINIMAP = "basketball-minimap"
BUCKET_COURTS = "basketball-panorama-warp"