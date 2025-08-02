import numpy as np
import cv2
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes
from s3_client import get_object_from_minio
import os

os.environ["PADDLEOCR_HOME"] = os.getenv("PADDLEOCR_HOME", "/usr/local/app/.paddleocr")

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='de',
)

def extract_text_from_s3(bucket: str, object_name: str) -> str:
    print(f"[OCR] Processing {bucket}/{object_name}")
    byte_data = get_object_from_minio(bucket, object_name)

    if object_name.lower().endswith(".pdf"):
        return extract_text_from_pdf(byte_data)
    else:
        return extract_text_from_image(byte_data)
    
def extract_text_from_image(byte_data: bytes):
    np_array = np.frombuffer(byte_data, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("Failed to decode image")

    result = ocr.ocr(image)
    if not result or not result[0]:
        print("[OCR] No text found in image.")
        return ""

    text_lines = [line[1][0] for line in result[0]]
    return " ".join(text_lines)

def extract_text_from_pdf(byte_data: bytes):
    images = convert_from_bytes(byte_data)
    if not images:
        raise ValueError("Failed to convert PDF to images")

    text_parts = []
    for img in images:
        cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        result = ocr.ocr(cv_image)
        if result and result[0]:
            text_parts.extend([line[1][0] for line in result[0]])

    if not text_parts:
        print("[OCR] No text found in image.") 
        return ""

    return " ".join(text_parts)