"""Tests for storage client functionality using Factory Pattern."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestStorageClientFactory:
    """Test cases for StorageClientFactory."""

    def test_factory_create_minio_client(self):
        """Test factory creates MinIO client for LOCAL type."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules to pick up new env vars
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            from core.storage.client import StorageClientFactory
            from storage.minio.client import MinioStorageClient
            
            client = StorageClientFactory.create(type="LOCAL")
            
            assert isinstance(client, MinioStorageClient)

    def test_factory_create_azure_client(self):
        """Test factory creates Azure Storage client for AZURE type."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'STORAGE_CONNECTION_STRING': 'DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod:
                    del sys.modules[mod]
            
            from core.storage.client import StorageClientFactory
            from storage.storageaccount.client import AzureStorageClient
            
            with patch('azure.storage.blob.BlobServiceClient') as MockBlobService:
                MockBlobService.from_connection_string.return_value = Mock()
                
                client = StorageClientFactory.create(type="AZURE")
                
                assert isinstance(client, AzureStorageClient)

    def test_factory_invalid_type_raises_error(self):
        """Test factory raises ValueError for unsupported type."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod:
                    del sys.modules[mod]
            
            from core.storage.client import StorageClientFactory
            
            with pytest.raises(ValueError, match="Unsupported storage provider type"):
                StorageClientFactory.create(type="INVALID_TYPE")

    def test_factory_default_type_is_local(self):
        """Test factory defaults to LOCAL type."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            from core.storage.client import StorageClientFactory
            from storage.minio.client import MinioStorageClient
            
            client = StorageClientFactory.create()  # No type specified
            
            assert isinstance(client, MinioStorageClient)


class TestMinioStorageClient:
    """Test cases for MinioStorageClient."""

    def test_get_object_success(self):
        """Test successful object retrieval from MinIO."""
        test_data = b'test file content'
        
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            with patch('storage.minio.client.Minio') as MockMinio:
                # Setup mock response
                mock_response = Mock()
                mock_response.read.return_value = test_data
                
                mock_client = Mock()
                mock_client.get_object.return_value = mock_response
                MockMinio.return_value = mock_client
                
                from storage.minio.client import MinioStorageClient
                
                storage = MinioStorageClient()
                result = storage.get_object('test-bucket', 'test-file.txt')
                
                assert result == test_data
                mock_client.get_object.assert_called_once_with('test-bucket', 'test-file.txt')
                mock_response.close.assert_called_once()
                mock_response.release_conn.assert_called_once()

    def test_get_object_error(self):
        """Test handling of MinIO errors during get_object."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            with patch('storage.minio.client.Minio') as MockMinio:
                mock_client = Mock()
                mock_client.get_object.side_effect = Exception("MinIO connection error")
                MockMinio.return_value = mock_client
                
                from storage.minio.client import MinioStorageClient
                
                storage = MinioStorageClient()
                
                with pytest.raises(Exception, match="MinIO connection error"):
                    storage.get_object('test-bucket', 'test-file.txt')

    def test_get_object_empty_file(self):
        """Test handling of empty files."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            with patch('storage.minio.client.Minio') as MockMinio:
                mock_response = Mock()
                mock_response.read.return_value = b''
                
                mock_client = Mock()
                mock_client.get_object.return_value = mock_response
                MockMinio.return_value = mock_client
                
                from storage.minio.client import MinioStorageClient
                
                storage = MinioStorageClient()
                result = storage.get_object('test-bucket', 'empty-file.txt')
                
                assert result == b''
                mock_response.close.assert_called_once()
                mock_response.release_conn.assert_called_once()

    def test_get_object_large_file(self):
        """Test handling of large files."""
        # Simulate a large file (1MB)
        test_data = b'x' * (1024 * 1024)
        
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            with patch('storage.minio.client.Minio') as MockMinio:
                mock_response = Mock()
                mock_response.read.return_value = test_data
                
                mock_client = Mock()
                mock_client.get_object.return_value = mock_response
                MockMinio.return_value = mock_client
                
                from storage.minio.client import MinioStorageClient
                
                storage = MinioStorageClient()
                result = storage.get_object('test-bucket', 'large-file.bin')
                
                assert result == test_data
                assert len(result) == 1024 * 1024

    def test_put_object_success(self):
        """Test successful object upload to MinIO."""
        test_data = b'test file content'
        
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test-access-key',
            'MINIO_SECRET_KEY': 'test-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            with patch('storage.minio.client.Minio') as MockMinio:
                mock_client = Mock()
                MockMinio.return_value = mock_client
                
                from storage.minio.client import MinioStorageClient
                
                storage = MinioStorageClient()
                storage.put_object(
                    'test-bucket',
                    'test-file.txt',
                    test_data,
                    len(test_data),
                    'text/plain'
                )
                
                mock_client.put_object.assert_called_once()
                call_args = mock_client.put_object.call_args
                assert call_args[0][0] == 'test-bucket'
                assert call_args[0][1] == 'test-file.txt'

    def test_client_initialization_with_secrets(self):
        """Test that client correctly retrieves secrets during initialization."""
        with patch.dict(os.environ, {
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'custom-endpoint:9000',
            'MINIO_ACCESS_KEY': 'custom-access-key',
            'MINIO_SECRET_KEY': 'custom-secret-key'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'storage' in mod or 'vault' in mod or 'minio' in mod:
                    del sys.modules[mod]
            
            with patch('storage.minio.client.Minio') as MockMinio:
                MockMinio.return_value = Mock()
                
                from storage.minio.client import MinioStorageClient
                
                storage = MinioStorageClient()
                
                assert storage.endpoint == 'custom-endpoint:9000'
                assert storage.access_key == 'custom-access-key'
                assert storage.secret_key == 'custom-secret-key'
                
                # Verify Minio was initialized with correct params
                MockMinio.assert_called_once_with(
                    'custom-endpoint:9000',
                    access_key='custom-access-key',
                    secret_key='custom-secret-key',
                    secure=False
                )
