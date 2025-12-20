"""Download and initialize PaddleOCR models.

This script downloads the PaddleOCR model files needed for German OCR.
It should be run during Docker image build or initial setup to cache
the models locally in ~/.paddleocr/

The downloaded models include:
- Detection model for finding text regions
- Recognition model for German language text
- Angle classification model for text orientation correction
"""

from paddleocr import PaddleOCR

# Initialize PaddleOCR to download and cache models in ~/.paddleocr/
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='de',
)
