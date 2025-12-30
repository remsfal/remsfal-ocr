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

# Load environment variables FIRST before any other imports that use them
load_dotenv()

# Add src directory to path to import factory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from core.kafka.client import KafkaConsumerFactory, KafkaProducerFactory
from core.storage.client import StorageClientFactory

# Get configuration from environment (not secrets)
TOPIC_IN = os.getenv("KAFKA_TOPIC_IN", "ocr.documents.to_process")
TOPIC_OUT = os.getenv("KAFKA_TOPIC_OUT", "ocr.documents.processed")
STORAGE_PROVIDER = os.getenv("STORAGE_PROVIDER", "LOCAL")
KAFKA_PROVIDER = os.getenv("KAFKA_PROVIDER", "LOCAL")


def upload_test_image(bucket_name: str, file_path: str):
    """Upload a test image to storage using the Factory Pattern."""
    print(f"Uploading {file_path} to storage bucket/container '{bucket_name}'...")

    # Create storage client using factory with provider type
    storage_client = StorageClientFactory.create(type=STORAGE_PROVIDER)


    # Read file data
    file_name = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    # Upload to storage
    storage_client.put_object(
        bucket_name,
        file_name,
        file_data,
        len(file_data)
    )

    print(f"Uploaded '{file_name}' to bucket/container '{bucket_name}'")
    return file_name


def send_ocr_request(bucket_name: str, file_name: str):
    """Send OCR request to Kafka."""
    print(f"\nSending OCR request to Kafka topic '{TOPIC_IN}'...")

    producer = KafkaProducerFactory.create(type=KAFKA_PROVIDER)

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

    # Note: consumer_timeout_ms is not supported by factory, using default session_timeout_ms
    consumer = KafkaConsumerFactory.create(
        topic=TOPIC_OUT,
        group_id='test-consumer',
        type=KAFKA_PROVIDER,
        session_timeout_ms=timeout_ms
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
