"""Storage client factory.

This module provides a factory for creating storage clients based on
the configured storage provider (MinIO, Azure Storage Account, etc.).
"""

import logging

from core.storage.base import StorageClient
from storage.minio.client import MinioStorageClient
from storage.storageaccount.client import AzureStorageClient

logger = logging.getLogger(__name__)


class StorageClientFactory:
    """Factory class to create storage clients based on the provider."""

    @staticmethod
    def create(type: str = "LOCAL") -> StorageClient:
        """Create and return a storage client based on the provider type.

        Args:
            type: The storage provider type. Supported values:
                  - LOCAL: Uses MinIO storage
                  - AZURE: Uses Azure Storage Account

        Returns:
            StorageClient: Configured storage client instance

        Raises:
            ValueError: If an unsupported storage provider type is specified
        """
        if type == "AZURE":
            logger.info("Creating Azure Storage client")
            return AzureStorageClient()
        elif type == "LOCAL":
            logger.info("Creating MinIO Storage client")
            return MinioStorageClient()
        else:
            raise ValueError(
                f"Unsupported storage provider type: {type}. "
                f"Supported types: LOCAL, AZURE"
            )
