"""Tests for OCR engine functionality."""

import pytest
import numpy as np
import cv2
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


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
        
        # Mock the S3 client and OCR response
        mock_ocr_result = [
            [
                [[[10, 10], [100, 10], [100, 50], [10, 50]], ('Sample text', 0.95)],
                [[[120, 10], [200, 10], [200, 50], [120, 50]], ('extracted', 0.93)]
            ]
        ]
        
        with patch.dict('sys.modules', {'paddleocr': Mock()}), \
             patch('ocr_engine.get_object_from_minio') as mock_get_object, \
             patch('ocr_engine.ocr') as mock_ocr:
            
            from ocr_engine import extract_text_from_s3
            
            mock_get_object.return_value = test_image_bytes
            mock_ocr.ocr.return_value = mock_ocr_result
            
            result = extract_text_from_s3('test-bucket', 'test-image.png')
            
            assert result == 'Sample text extracted'
            mock_get_object.assert_called_once_with('test-bucket', 'test-image.png')
            mock_ocr.ocr.assert_called_once()

    def test_extract_text_from_s3_invalid_image(self):
        """Test handling of invalid image data."""
        # Invalid image bytes
        invalid_image_bytes = b'invalid image data'
        
        with patch.dict('sys.modules', {'paddleocr': Mock()}), \
             patch('ocr_engine.get_object_from_minio') as mock_get_object:
            
            from ocr_engine import extract_text_from_s3
            
            mock_get_object.return_value = invalid_image_bytes
            
            result = extract_text_from_s3('test-bucket', 'invalid-image.png')
            
            assert result == ""
            mock_get_object.assert_called_once_with('test-bucket', 'invalid-image.png')

    def test_extract_text_from_s3_no_text_found(self):
        """Test handling when no text is found in image."""
        # Create a simple test image with no text
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image.fill(255)  # White background only
        
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        with patch.dict('sys.modules', {'paddleocr': Mock()}), \
             patch('ocr_engine.get_object_from_minio') as mock_get_object, \
             patch('ocr_engine.ocr') as mock_ocr:
            
            from ocr_engine import extract_text_from_s3
            
            mock_get_object.return_value = test_image_bytes
            # Mock OCR returning empty result
            mock_ocr.ocr.return_value = []
            
            result = extract_text_from_s3('test-bucket', 'empty-image.png')
            
            assert result == ""
            mock_get_object.assert_called_once_with('test-bucket', 'empty-image.png')

    def test_extract_text_from_s3_ocr_none_result(self):
        """Test handling when OCR returns None."""
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image.fill(255)
        
        _, img_encoded = cv2.imencode('.png', test_image)
        test_image_bytes = img_encoded.tobytes()
        
        with patch.dict('sys.modules', {'paddleocr': Mock()}), \
             patch('ocr_engine.get_object_from_minio') as mock_get_object, \
             patch('ocr_engine.ocr') as mock_ocr:
            
            from ocr_engine import extract_text_from_s3
            
            mock_get_object.return_value = test_image_bytes
            mock_ocr.ocr.return_value = None
            
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
        
        with patch.dict('sys.modules', {'paddleocr': Mock()}), \
             patch('ocr_engine.get_object_from_minio') as mock_get_object, \
             patch('ocr_engine.ocr') as mock_ocr:
            
            from ocr_engine import extract_text_from_s3
            
            mock_get_object.return_value = test_image_bytes
            mock_ocr.ocr.return_value = mock_ocr_result
            
            result = extract_text_from_s3('test-bucket', 'single-word.png')
            
            assert result == 'Hello'

    def test_extract_text_from_s3_s3_error(self):
        """Test handling of S3 errors."""
        with patch.dict('sys.modules', {'paddleocr': Mock()}), \
             patch('ocr_engine.get_object_from_minio') as mock_get_object:
            
            from ocr_engine import extract_text_from_s3
            
            mock_get_object.side_effect = Exception("S3 connection error")
            
            with pytest.raises(Exception, match="S3 connection error"):
                extract_text_from_s3('test-bucket', 'test-image.png')