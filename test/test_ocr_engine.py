"""Tests for OCR engine functionality."""

import pytest
import numpy as np
import cv2
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def clear_ocr_modules():
    """Clear cached OCR-related modules to allow fresh imports with mocks."""
    for mod in list(sys.modules.keys()):
        if any(x in mod for x in ['ocr', 'storage', 'vault', 'paddle']):
            del sys.modules[mod]


class TestOCREngine:
    """Test cases for OCR engine functionality."""

    def test_extract_text_from_s3_success(self):
        """Test successful text extraction from S3 image."""
        # Create a simple test image (white background with black text)
        test_image = np.zeros((100, 400, 3), dtype=np.uint8)
        test_image.fill(255)  # White background
        # Add some text-like pattern
        cv2.rectangle(test_image, (50, 30), (350, 70), (0, 0, 0), -1)
        
        # Encode image to bytes
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        # Mock the OCR response
        mock_ocr_result = [
            [
                [[[10, 10], [100, 10], [100, 50], [10, 50]], ('Sample text', 0.95)],
                [[[120, 10], [200, 10], [200, 50], [120, 50]], ('extracted', 0.93)]
            ]
        ]
        
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            # Mock PaddleOCR before importing ocr_engine
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_ocr_instance.ocr.return_value = mock_ocr_result
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                # Mock the storage client
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.return_value = test_image_bytes
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    result = extract_text_from_s3('test-bucket', 'test-image.png')
                    
                    assert result == 'Sample text extracted'
                    mock_storage.get_object.assert_called_once_with('test-bucket', 'test-image.png')

    def test_extract_text_from_s3_invalid_image(self):
        """Test handling of invalid image data."""
        # Invalid image bytes
        invalid_image_bytes = b'invalid image data'
        
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.return_value = invalid_image_bytes
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    result = extract_text_from_s3('test-bucket', 'invalid-image.png')
                    
                    assert result == ""
                    mock_storage.get_object.assert_called_once_with('test-bucket', 'invalid-image.png')

    def test_extract_text_from_s3_no_text_found(self):
        """Test handling when no text is found in image."""
        # Create a simple test image with no text
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image.fill(255)  # White background only
        
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_ocr_instance.ocr.return_value = []  # Empty result
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.return_value = test_image_bytes
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    result = extract_text_from_s3('test-bucket', 'empty-image.png')
                    
                    assert result == ""
                    mock_storage.get_object.assert_called_once_with('test-bucket', 'empty-image.png')

    def test_extract_text_from_s3_ocr_none_result(self):
        """Test handling when OCR returns None."""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image.fill(255)
        
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_ocr_instance.ocr.return_value = None
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.return_value = test_image_bytes
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    result = extract_text_from_s3('test-bucket', 'test-image.png')
                    
                    assert result == ""

    def test_extract_text_from_s3_single_word(self):
        """Test extraction of single word."""
        test_image = np.zeros((50, 200, 3), dtype=np.uint8)
        test_image.fill(255)
        
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        mock_ocr_result = [
            [
                [[[10, 10], [100, 10], [100, 40], [10, 40]], ('Hello', 0.98)]
            ]
        ]
        
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_ocr_instance.ocr.return_value = mock_ocr_result
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.return_value = test_image_bytes
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    result = extract_text_from_s3('test-bucket', 'single-word.png')
                    
                    assert result == 'Hello'

    def test_extract_text_from_s3_storage_error(self):
        """Test handling of storage errors."""
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.side_effect = Exception("Storage connection error")
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    with pytest.raises(Exception, match="Storage connection error"):
                        extract_text_from_s3('test-bucket', 'test-image.png')

    def test_extract_text_from_s3_multiline_text(self):
        """Test extraction of multiple lines of text."""
        test_image = np.zeros((200, 400, 3), dtype=np.uint8)
        test_image.fill(255)
        
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        mock_ocr_result = [
            [
                [[[10, 10], [200, 10], [200, 40], [10, 40]], ('Line one', 0.95)],
                [[[10, 50], [200, 50], [200, 80], [10, 80]], ('Line two', 0.93)],
                [[[10, 90], [200, 90], [200, 120], [10, 120]], ('Line three', 0.91)]
            ]
        ]
        
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_ocr_instance = Mock()
            mock_ocr_instance.ocr.return_value = mock_ocr_result
            mock_paddle.PaddleOCR.return_value = mock_ocr_instance
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    mock_storage = Mock()
                    mock_storage.get_object.return_value = test_image_bytes
                    MockFactory.create.return_value = mock_storage
                    
                    from ocr_engine import extract_text_from_s3
                    
                    result = extract_text_from_s3('test-bucket', 'multiline.png')
                    
                    assert result == 'Line one Line two Line three'

    def test_storage_client_uses_factory(self):
        """Test that OCR engine uses StorageClientFactory."""
        with patch.dict(os.environ, {
            'STORAGE_PROVIDER': 'AZURE',
            'SECRETS_PROVIDER': 'LOCAL',
            'AZURE_STORAGE_ACCOUNT_URL': 'https://test.blob.core.windows.net'
        }):
            clear_ocr_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockFactory:
                    MockFactory.create.return_value = Mock()
                    
                    # Just importing should trigger factory creation
                    import ocr_engine
                    
                    MockFactory.create.assert_called_once_with(type='AZURE')
