"""Base interface for storage clients.

This module defines the abstract base class for storage operations,
providing a common interface for different storage providers (MinIO, Azure, etc.).
"""

from abc import ABC, abstractmethod


class StorageClient(ABC):
    """Abstract base class for storage client implementations.
    
    This interface defines the contract that all storage providers
    (MinIO, Azure Storage Account, etc.) must implement.
    """

    @abstractmethod
    def get_object(self, container_name: str, object_name: str) -> bytes:
        """Download an object from storage.

        Args:
            container_name: Name of the storage container/bucket
            object_name: Key/path of the object within the container

        Returns:
            bytes: Raw binary content of the downloaded object

        Raises:
            Exception: If the object cannot be downloaded
        """
        pass

    @abstractmethod
    def put_object(
        self,
        container_name: str,
        object_name: str,
        data: bytes,
        length: int,
        content_type: str = "application/octet-stream"
    ) -> None:
        """Upload an object to storage.

        Args:
            container_name: Name of the storage container/bucket
            object_name: Key/path for the object within the container
            data: Binary data to upload
            length: Size of the data in bytes
            content_type: MIME type of the content (default: application/octet-stream)

        Raises:
            Exception: If the object cannot be uploaded
        """
        pass
