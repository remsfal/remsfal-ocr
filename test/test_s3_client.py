"""Tests for S3 client functionality."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestS3Client:
    """Test cases for S3 client functionality."""

    def test_get_object_from_s3_success(self):
        """Test successful object retrieval from S3."""
        test_data = b'test file content'

        # Mock the S3 response
        mock_response = Mock()
        mock_response.read.return_value = test_data

        with patch.dict('sys.modules', {'minio': Mock()}), \
             patch('s3_client.client') as mock_client:

            from s3_client import get_object_from_s3

            mock_client.get_object.return_value = mock_response

            result = get_object_from_s3('test-bucket', 'test-file.txt')

            assert result == test_data
            mock_client.get_object.assert_called_once_with('test-bucket', 'test-file.txt')
            mock_response.read.assert_called_once()
            mock_response.close.assert_called_once()
            mock_response.release_conn.assert_called_once()

    def test_get_object_from_s3_error(self):
        """Test handling of S3 errors."""
        with patch.dict('sys.modules', {'minio': Mock()}), \
             patch('s3_client.client') as mock_client:

            from s3_client import get_object_from_s3

            mock_client.get_object.side_effect = Exception("S3 connection error")

            with pytest.raises(Exception, match="S3 connection error"):
                get_object_from_s3('test-bucket', 'test-file.txt')

            mock_client.get_object.assert_called_once_with('test-bucket', 'test-file.txt')

    def test_get_object_from_s3_read_error(self):
        """Test handling of read errors."""
        mock_response = Mock()
        mock_response.read.side_effect = Exception("Read error")

        with patch.dict('sys.modules', {'minio': Mock()}), \
             patch('s3_client.client') as mock_client:

            from s3_client import get_object_from_s3

            mock_client.get_object.return_value = mock_response

            with pytest.raises(Exception, match="Read error"):
                get_object_from_s3('test-bucket', 'test-file.txt')

    def test_get_object_from_s3_empty_file(self):
        """Test handling of empty files."""
        mock_response = Mock()
        mock_response.read.return_value = b''

        with patch.dict('sys.modules', {'minio': Mock()}), \
             patch('s3_client.client') as mock_client:

            from s3_client import get_object_from_s3

            mock_client.get_object.return_value = mock_response

            result = get_object_from_s3('test-bucket', 'empty-file.txt')

            assert result == b''
            mock_response.close.assert_called_once()
            mock_response.release_conn.assert_called_once()

    def test_get_object_from_s3_large_file(self):
        """Test handling of large files."""
        # Simulate a large file (1MB)
        test_data = b'x' * (1024 * 1024)

        mock_response = Mock()
        mock_response.read.return_value = test_data

        with patch.dict('sys.modules', {'minio': Mock()}), \
             patch('s3_client.client') as mock_client:

            from s3_client import get_object_from_s3

            mock_client.get_object.return_value = mock_response

            result = get_object_from_s3('test-bucket', 'large-file.bin')

            assert result == test_data
            assert len(result) == 1024 * 1024
