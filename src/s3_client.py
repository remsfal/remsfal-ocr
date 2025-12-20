"""MinIO/S3 client for object storage operations.

This module provides a client interface for interacting with MinIO
(S3-compatible object storage). It handles downloading objects from
configured buckets with proper connection management and error handling.
"""

import logging
from minio import Minio
import os

logger = logging.getLogger(__name__)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


def get_object_from_minio(bucket_name: str, object_name: str) -> bytes:
    """Download an object from MinIO/S3 bucket.

    Retrieves a file from the specified MinIO bucket and returns its
    contents as bytes. The function properly manages the HTTP connection
    lifecycle to prevent resource leaks.

    Args:
        bucket_name: Name of the MinIO bucket
        object_name: Key/path of the object within the bucket

    Returns:
        bytes: Raw binary content of the downloaded object

    Raises:
        Exception: If the object cannot be downloaded (bucket not found,
                  object not found, connection errors, permission errors, etc.)

    Example:
        >>> data = get_object_from_minio("documents", "invoice.pdf")
        >>> print(f"Downloaded {len(data)} bytes")
        Downloaded 45678 bytes
    """
    try:
        logger.info(f"Downloading {object_name} from bucket {bucket_name}...")
        response = client.get_object(bucket_name, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        logger.info(f"Downloaded {len(data)} bytes")
        return data
    except Exception as e:
        logger.error(f"Error fetching object: {e}")
        raise
