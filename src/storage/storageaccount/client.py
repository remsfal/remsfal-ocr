"""Azure Storage Account client implementation.

This module provides an Azure Storage Account-specific implementation
of the StorageClient interface for interacting with Azure Blob Storage.
"""

import logging
import os
from azure.storage.blob import BlobServiceClient, ContentSettings

from core.storage.base import StorageClient

logger = logging.getLogger(__name__)


class AzureStorageClient(StorageClient):
    """Azure Storage Account implementation of the storage client interface.
    
    Handles object storage operations using Azure Blob Storage.
    """

    def __init__(self):
        """Initialize Azure Storage client with configuration from environment variables."""
        self.connection_string = os.getenv("STORAGE_CONNECTION_STRING")
        
        if not self.connection_string:
            raise ValueError("STORAGE_CONNECTION_STRING environment variable is required for Azure storage")
        
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        logger.info("Azure Storage client initialized")

    def get_object(self, container_name: str, object_name: str) -> bytes:
        """Download an object from Azure Blob Storage.

        Retrieves a blob from the specified container and returns its
        contents as bytes.

        Args:
            container_name: Name of the Azure Blob Storage container
            object_name: Key/path of the blob within the container

        Returns:
            bytes: Raw binary content of the downloaded blob

        Raises:
            Exception: If the blob cannot be downloaded (container not found,
                      blob not found, connection errors, permission errors, etc.)
        """
        try:
            logger.info(f"Downloading {object_name} from container {container_name}...")
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=object_name
            )
            
            data = blob_client.download_blob().readall()
            logger.info(f"Downloaded {len(data)} bytes")
            return data
        except Exception as e:
            logger.error(f"Error fetching object from Azure Storage: {e}")
            raise

    def put_object(
        self,
        container_name: str,
        object_name: str,
        data: bytes,
        length: int,
        content_type: str = "application/octet-stream"
    ) -> None:
        """Upload an object to Azure Blob Storage.

        Uploads binary data to the specified container.

        Args:
            container_name: Name of the Azure Blob Storage container
            object_name: Key/path for the blob within the container
            data: Binary data to upload
            length: Size of the data in bytes (not used by Azure SDK but kept for interface compatibility)
            content_type: MIME type of the content (default: application/octet-stream)

        Raises:
            Exception: If the blob cannot be uploaded (container not found,
                      permission errors, etc.)
        """
        try:
            logger.info(f"Uploading {object_name} to container {container_name} ({length} bytes)...")
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=object_name
            )
            
            content_settings = ContentSettings(content_type=content_type)
            
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=content_settings
            )
            logger.info(f"Successfully uploaded {object_name}")
        except Exception as e:
            logger.error(f"Error uploading object to Azure Storage: {e}")
            raise
