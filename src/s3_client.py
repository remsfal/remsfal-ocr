"""S3 client for object storage operations.

This module provides a client interface for interacting with S3-compatible
object storage (LocalStack for local development, IONOS S3 in production).
It handles downloading objects from configured buckets with proper
connection management and error handling.
"""

import logging
from minio import Minio
import os

logger = logging.getLogger(__name__)

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "localhost:4566")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadminpassword")

client = Minio(
    S3_ENDPOINT,
    access_key=S3_ACCESS_KEY,
    secret_key=S3_SECRET_KEY,
    secure=False
)


def get_object_from_s3(bucket_name: str, object_name: str) -> bytes:
    """Download an object from an S3-compatible bucket.

    Retrieves a file from the specified bucket and returns its
    contents as bytes. The function properly manages the HTTP connection
    lifecycle to prevent resource leaks.

    Args:
        bucket_name: Name of the S3 bucket
        object_name: Key/path of the object within the bucket

    Returns:
        bytes: Raw binary content of the downloaded object

    Raises:
        Exception: If the object cannot be downloaded (bucket not found,
                  object not found, connection errors, permission errors, etc.)

    Example:
        >>> data = get_object_from_s3("documents", "invoice.pdf")
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
