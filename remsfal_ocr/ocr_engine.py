import os
from s3_client import get_object_from_minio
from paddleocr import PaddleOCR
from pdf2image import convert_from_bytes

USE_GPU = os.getenv("USE_GPU", "false")

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='de',
    use_gpu=USE_GPU,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

def extract_text_from_s3(bucket: str, object_name: str) -> str:
    print(f"[OCR] Processing {bucket}/{object_name}")
    file_stream = get_object_from_minio(bucket, object_name)
    content = file_stream.read()

    return extract_text_from_image_bytes(content)


def extract_text_from_image_bytes(img_bytes: bytes) -> str:
    result = ocr.ocr(img_bytes, cls=True)
    if not result or not result[0]:
        print("[OCR] No text found in image.")
        return ""
    text_lines = [line[1][0] for line in result[0]]
    return "\n".join(text_lines)