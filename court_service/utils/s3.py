import os
import boto3
import uuid

BUCKET = os.getenv("S3_BUCKET_NAME", "court-homography-bucket")

def upload_to_s3(path, key_prefix, job_id=None):
    s3 = boto3.client("s3")

    if not job_id:
        job_id = str(uuid.uuid4())

    key = f"{key_prefix}/{uuid.uuid4()}.jpg"
    s3.upload_file(path, BUCKET, key)

    return f"s3://{BUCKET}/{key}"