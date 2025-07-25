from paddleocr import PaddleOCR

# install models in ~/.paddleocr/
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='de',
)
