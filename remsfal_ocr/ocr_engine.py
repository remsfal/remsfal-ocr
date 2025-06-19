import numpy as np
import cv2
from paddleocr import PaddleOCR
from s3_client import get_object_from_minio

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='de',
)

def extract_text_from_s3(bucket: str, object_name: str) -> str:
    print(f"[OCR] Processing {bucket}/{object_name}")
    byte_data = get_object_from_minio(bucket, object_name)
    np_array = np.frombuffer(byte_data, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if image is None:
        print("[OCR] Failed to decode image.")
        return ""

    result = ocr.ocr(image)
    if not result or not result[0]:
        print("[OCR] No text found in image.")
        return ""

    text_lines = [line[1][0] for line in result[0]]
    return " ".join(text_lines)
