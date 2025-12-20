#!/usr/bin/env python3
"""
Test script to send messages to Kafka and test OCR functionality.
Prerequisites:
- Docker services running (docker compose -f docker-compose.dev.yml up)
- An image file uploaded to MinIO bucket 'documents'
"""
import json
import os
import sys
from dotenv import load_dotenv
from kafka import KafkaProducer, KafkaConsumer
from minio import Minio

# Load environment variables from .env file
load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC_IN = os.getenv("KAFKA_TOPIC_IN", "ocr.documents.to_process")
TOPIC_OUT = os.getenv("KAFKA_TOPIC_OUT", "ocr.documents.processed")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")


def upload_test_image(bucket_name: str, file_path: str):
    """Upload a test image to MinIO."""
    print(f"Uploading {file_path} to MinIO bucket '{bucket_name}'...")

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )

    # Create bucket if it doesn't exist
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Created bucket '{bucket_name}'")

    # Upload file
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as file_data:
        file_stat = os.stat(file_path)
        client.put_object(
            bucket_name,
            file_name,
            file_data,
            file_stat.st_size
        )

    print(f"Uploaded '{file_name}' to bucket '{bucket_name}'")
    return file_name


def send_ocr_request(bucket_name: str, file_name: str):
    """Send OCR request to Kafka."""
    print(f"\nSending OCR request to Kafka topic '{TOPIC_IN}'...")

    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    message = {
        "sessionId": "test-session-123",
        "messageId": "test-message-456",
        "bucket": bucket_name,
        "fileName": file_name
    }

    producer.send(TOPIC_IN, message)
    producer.flush()
    print(f"Sent message: {message}")


def listen_for_results(timeout_ms: int = 30000):
    """Listen for OCR results from Kafka."""
    print(f"\nListening for results on topic '{TOPIC_OUT}'...")

    consumer = KafkaConsumer(
        TOPIC_OUT,
        group_id='test-consumer',
        bootstrap_servers=[KAFKA_BROKER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        consumer_timeout_ms=timeout_ms
    )

    for message in consumer:
        result = message.value
        print("\nReceived OCR result:")
        print(json.dumps(result, indent=2))
        break
    else:
        print(f"No results received within {timeout_ms/1000}s timeout")

    consumer.close()


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/test_ocr.py <image_file_path>")
        print("\nExample:")
        print("  python scripts/test_ocr.py test_image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    if not os.path.exists(image_path):
        print(f"Error: File '{image_path}' not found")
        sys.exit(1)

    bucket_name = "documents"

    try:
        # Upload test image
        file_name = upload_test_image(bucket_name, image_path)

        # Send OCR request
        send_ocr_request(bucket_name, file_name)

        # Listen for results
        listen_for_results()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
