"""Storage client factory.

This module provides a factory for creating storage clients based on
the configured storage provider (MinIO, Azure Storage Account, etc.).
"""

import logging
import os

from core.storage.base import StorageClient
from storage.minio.client import MinioStorageClient
from storage.storageaccount.client import AzureStorageClient

logger = logging.getLogger(__name__)

STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "LOCAL")


class StorageClientFactory:
    """Factory class to create storage clients based on the provider."""

    @staticmethod
    def create() -> StorageClient:
        """Create and return a storage client based on the provider.

        The provider is determined by the STORAGE_PROVIDER environment variable.
        Supported values:
        - LOCAL: Uses MinIO storage
        - AZURE: Uses Azure Storage Account

        Returns:
            StorageClient: Configured storage client instance

        Raises:
            ValueError: If an unsupported storage provider is specified
        """
        if STORAGE_PROVIDER == "AZURE":
            logger.info("Creating Azure Storage client")
            return AzureStorageClient()
        elif STORAGE_PROVIDER == "LOCAL":
            logger.info("Creating MinIO Storage client")
            return MinioStorageClient()
        else:
            raise ValueError(
                f"Unsupported storage provider: {STORAGE_PROVIDER}. "
                f"Supported providers: LOCAL, AZURE"
            )
