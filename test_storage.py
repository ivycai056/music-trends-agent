
import os
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

bucket_name = os.getenv("GCS_BUCKET_NAME")

if not bucket_name:
    raise ValueError("GCS_BUCKET_NAME is missing from .env")

print("Connecting to Google Cloud Storage...")

client = storage.Client()
bucket = client.bucket(bucket_name)

test_data = {
    "project": "Music Trends Analytics Agent",
    "status": "Success",
    "timestamp": datetime.now(timezone.utc).isoformat()
}

blob = bucket.blob("test/test_upload.json")

blob.upload_from_string(
    json.dumps(test_data, indent=2),
    content_type="application/json"
)

print("Upload successful!")
print(f"File saved to gs://{bucket_name}/test/test_upload.json")
