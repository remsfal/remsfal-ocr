"""MinIO storage client implementation.

This module provides a MinIO-specific implementation of the StorageClient
interface for interacting with MinIO (S3-compatible object storage).
"""

import logging
import os
from minio import Minio

from core.storage.base import StorageClient

logger = logging.getLogger(__name__)


class MinioStorageClient(StorageClient):
    """MinIO implementation of the storage client interface.
    
    Handles object storage operations using MinIO (S3-compatible storage).
    """

    def __init__(self):
        """Initialize MinIO client with configuration from environment variables."""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )
        logger.info(f"MinIO client initialized with endpoint: {self.endpoint}")

    def get_object(self, container_name: str, object_name: str) -> bytes:
        """Download an object from MinIO bucket.

        Retrieves a file from the specified MinIO bucket and returns its
        contents as bytes. The function properly manages the HTTP connection
        lifecycle to prevent resource leaks.

        Args:
            container_name: Name of the MinIO bucket
            object_name: Key/path of the object within the bucket

        Returns:
            bytes: Raw binary content of the downloaded object

        Raises:
            Exception: If the object cannot be downloaded (bucket not found,
                      object not found, connection errors, permission errors, etc.)
        """
        try:
            logger.info(f"Downloading {object_name} from bucket {container_name}...")
            response = self.client.get_object(container_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Downloaded {len(data)} bytes")
            return data
        except Exception as e:
            logger.error(f"Error fetching object from MinIO: {e}")
            raise

    def put_object(
        self,
        container_name: str,
        object_name: str,
        data: bytes,
        length: int,
        content_type: str = "application/octet-stream"
    ) -> None:
        """Upload an object to MinIO bucket.

        Uploads binary data to the specified MinIO bucket.

        Args:
            container_name: Name of the MinIO bucket
            object_name: Key/path for the object within the bucket
            data: Binary data to upload
            length: Size of the data in bytes
            content_type: MIME type of the content (default: application/octet-stream)

        Raises:
            Exception: If the object cannot be uploaded (bucket not found,
                      permission errors, etc.)
        """
        try:
            logger.info(f"Uploading {object_name} to bucket {container_name} ({length} bytes)...")
            
            # MinIO requires a file-like object, so we wrap bytes in BytesIO
            from io import BytesIO
            data_stream = BytesIO(data)
            
            self.client.put_object(
                container_name,
                object_name,
                data_stream,
                length,
                content_type=content_type
            )
            logger.info(f"Successfully uploaded {object_name}")
        except Exception as e:
            logger.error(f"Error uploading object to MinIO: {e}")
            raise
