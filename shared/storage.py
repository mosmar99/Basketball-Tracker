import os
import boto3
import tempfile
from botocore.client import Config
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

local_minio_key = os.getenv("MINIO_ENDPOINT")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", local_minio_key)
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

def bucket_exists(s3, BUCKET_NAME):
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    if BUCKET_NAME not in buckets:
        return False
    else:
        return True

def upload_video(local_path, key, BUCKET_NAME="basketball"):
    s3 = get_s3()

    if not bucket_exists(s3, BUCKET_NAME):
        s3.create_bucket(Bucket=BUCKET_NAME)

    print(f"Uploading {local_path} to bucket={BUCKET_NAME}, key={key}")
    s3.upload_file(local_path, BUCKET_NAME, key)

    print("Upload complete!")
    return f"s3://{BUCKET_NAME}/{key}"

def s3_upload(local_path, key, BUCKET_NAME="basketball"):
    s3 = get_s3()

    if not bucket_exists(s3, BUCKET_NAME):
        s3.create_bucket(Bucket=BUCKET_NAME)

    print(f"Uploading {local_path} to bucket={BUCKET_NAME}, key={key}")
    s3.upload_file(local_path, BUCKET_NAME, key)

    print("Upload complete!")
    return f"s3://{BUCKET_NAME}/{key}"

def delete_video(key, BUCKET_NAME="basketball"):
    s3 = get_s3()

    if not bucket_exists(s3, BUCKET_NAME):
        print(f"Bucket {BUCKET_NAME} does not exist, nothing to delete.")
        return None

    print(f"Deleting key={key} from bucket={BUCKET_NAME}")
    s3.delete_object(Bucket=BUCKET_NAME, Key=key)

    print("Delete complete!")
    return f"s3://{BUCKET_NAME}/{key}"

def delete_bucket(BUCKET_NAME="basketball"):
    s3 = get_s3()

    if not bucket_exists(s3, BUCKET_NAME):
        print(f"Bucket {BUCKET_NAME} does not exist, nothing to delete.")
        return None

    print(f"Deleting all objects in bucket={BUCKET_NAME}...")

    # Delete all objects in the bucket
    while True:
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME)
        contents = resp.get("Contents", [])
        if not contents:
            break

        objects = [{"Key": obj["Key"]} for obj in contents]
        s3.delete_objects(
            Bucket=BUCKET_NAME,
            Delete={"Objects": objects, "Quiet": True},
        )

        if not resp.get("IsTruncated"):
            break

    print(f"Deleting bucket={BUCKET_NAME}...")
    s3.delete_bucket(Bucket=BUCKET_NAME)
    print("Bucket delete complete!")
    return BUCKET_NAME

def download_to_temp(key, bucket):
    s3 = get_s3()

    # Make a temp file with same extension as the key
    _, ext = os.path.splitext(key)
    fd, tmp_path = tempfile.mkstemp(suffix=ext)
    os.close(fd)

    print(f"Downloading s3://{bucket}/{key} -> {tmp_path}")
    s3.download_file(bucket, key, tmp_path)
    print("Download complete!")

    return tmp_path