import json
import os
from kafka import KafkaConsumer, KafkaProducer
from ocr_engine import extract_text_from_s3

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_IN = os.getenv("KAFKA_TOPIC_IN", "ocr.documents.to_process")
TOPIC_OUT = os.getenv("KAFKA_TOPIC_OUT", "ocr.documents.processed")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "ocr-service")

def start_kafka_listener():

    consumer = KafkaConsumer(
        TOPIC_IN,
        group_id=GROUP_ID,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset='earliest',
    )

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    print(f"[OCR] Listening to topic '{TOPIC_IN}'...")

    for message in consumer:
        try:
            payload = message.value
            print(f"[OCR] Received: {payload}")

            bucket = payload["bucket"]
            file_name = payload["fileName"]

            extracted_text = extract_text_from_s3(bucket, file_name)

            result = {
                "sessionId": payload["sessionId"],
                "messageId": payload["messageId"],
                "extractedText": extracted_text
            }

            producer.send(TOPIC_OUT, result)
            print(f"[OCR] Published result to '{TOPIC_OUT}': {result}")

        except Exception as e:
            print(f"[OCR] Error processing message: {e}")
