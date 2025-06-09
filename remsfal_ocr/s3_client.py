from minio import Minio
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def get_object_from_minio(bucket_name: str, object_name: str):
    try:
        print(f"[MinIO] Downloading {object_name} from bucket {bucket_name}...")
        return client.get_object(bucket_name, object_name)
    
    except Exception as e:
        print(f"[MinIO] Error fetching object: {e}")
        raise