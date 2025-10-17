import json
import os
import time
from kafka import KafkaConsumer, KafkaProducer
from ocr_engine import extract_text_from_s3

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:39092")
TOPIC_IN = os.getenv("KAFKA_TOPIC_IN", "ocr.documents.to_process")
TOPIC_OUT = os.getenv("KAFKA_TOPIC_OUT", "ocr.documents.processed")
TOPIC_DLQ = os.getenv("KAFKA_TOPIC_DLQ", "ocr.documents.dlq")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "ocr-service")

ALLOWED_FILETYPES = {".jpeg", ".jpg", ".png", ".pdf"}

def start_kafka_listener():
    retries = 25
    delay = 5  # seconds

    for attempt in range(retries):
        try:
            consumer = KafkaConsumer(
                TOPIC_IN,
                group_id=GROUP_ID,
                bootstrap_servers=KAFKA_BROKER,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                session_timeout_ms=30000,
            )
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print(f"[OCR] Listening to topic '{TOPIC_IN}'...")
            break
        except:
            print(f"[OCR] Kafka not reachable, retrying in {delay}s... ({attempt + 1}/{retries})")
            time.sleep(delay)
    else:
        raise Exception("Kafka could not be reached after several attempts")

    for message in consumer:
        try:
            payload = message.value
            print(f"[OCR] Received: {payload}")

            bucket = payload["bucket"]
            file_name = payload["fileName"]

            if not is_supported_file(file_name):
                print(f"[OCR] Skipping unsupported file type: {file_name}")
                continue

            extracted_text = extract_text_from_s3(bucket, file_name)

            if not extracted_text.strip():
                print("[OCR] No text found. Skipping message.")
                continue

            result = {
                "sessionId": payload["sessionId"],
                "messageId": payload["messageId"],
                "extractedText": extracted_text
            }

            producer.send(TOPIC_OUT, result)
            print(f"[OCR] Published result to '{TOPIC_OUT}': {result}")

        except Exception as e:
            print(f"[OCR] Error processing message: {e}")

            dlq_message = {
                "originalPayload": payload,
                "error": str(e)
            }
            producer.send(TOPIC_DLQ, dlq_message)
            print(f"[OCR] Sent message to DLQ '{TOPIC_DLQ}': {dlq_message}")

def is_supported_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_FILETYPES)
