import requests
import tempfile
import shutil
from .config import BUCKET_COURTS
from shared.storage import list_bucket_contents

def fetch_local_resource(url, suffix=""):
    if not url: return None
    try:
        with requests.get(url, stream=True) as r:
            if r.status_code == 200:
                t = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                with open(t.name, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                return t.name
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def list_courts():
    try:
        return list_bucket_contents(BUCKET_COURTS)
    except:
        return []