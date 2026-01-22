"""OCR text extraction engine using PaddleOCR.

This module provides OCR (Optical Character Recognition) functionality
for extracting text from images stored in S3/MinIO. It uses PaddleOCR
with German language support and automatic text orientation detection.
"""

import logging
import numpy as np
import cv2
from paddleocr import PaddleOCR
from core.storage.client import StorageClientFactory
import os

logger = logging.getLogger(__name__)

os.environ["PADDLEOCR_HOME"] = os.getenv("PADDLEOCR_HOME", "/usr/local/app/.paddleocr")

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='de',
)

# Get storage provider from environment (not a secret)
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "LOCAL")

# Initialize storage client using factory
storage_client = StorageClientFactory.create(type=STORAGE_PROVIDER)


def extract_text_from_s3(bucket: str, object_name: str) -> str:
    """Extract text from an image stored in S3/MinIO using OCR.

    Downloads an image from S3, decodes it, and performs OCR text extraction
    using PaddleOCR. The function handles various edge cases including
    invalid images and images without detectable text.

    Args:
        bucket: Name of the S3 bucket containing the image
        object_name: Name/key of the image file in the bucket

    Returns:
        str: Extracted text from the image, with text lines joined by spaces.
             Returns empty string if image is invalid or contains no text.

    Raises:
        IOError: If the object cannot be downloaded from S3
        OSError: If there are file system access errors

    Example:
        >>> text = extract_text_from_s3("documents", "invoice.pdf")
        >>> print(text)
        "Invoice Number 12345 Date 2024-01-01"
    """
    logger.info(f"Processing {bucket}/{object_name}")
    byte_data = storage_client.get_object(bucket, object_name)
    np_array = np.frombuffer(byte_data, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if image is None:
        logger.warning("Failed to decode image.")
        return ""

    result = ocr.ocr(image)
    if not result or not result[0]:
        logger.info("No text found in image.")
        return ""

    text_lines = [line[1][0] for line in result[0]]
    return " ".join(text_lines)
