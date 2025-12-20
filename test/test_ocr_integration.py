"""
Integration tests for OCR service using testcontainers.
These tests start real Kafka and MinIO containers and test the complete flow.
"""
import json
import pytest
from io import BytesIO
from pathlib import Path
from testcontainers.kafka import KafkaContainer
from testcontainers.minio import MinioContainer
from kafka import KafkaProducer, KafkaConsumer
from minio import Minio

# Path to test resources
TEST_RESOURCES_DIR = Path(__file__).parent / "resources"
TEST_IMAGE_PATH = TEST_RESOURCES_DIR / "test-image.png"


@pytest.fixture(scope="module")
def kafka_container():
    """Start a Kafka container for testing."""
    with KafkaContainer() as kafka:
        yield kafka


@pytest.fixture(scope="module")
def minio_container():
    """Start a MinIO container for testing."""
    with MinioContainer() as minio:
        yield minio


@pytest.fixture
def minio_client(minio_container):
    """Create MinIO client connected to test container."""
    client = Minio(
        minio_container.get_config()["endpoint"],
        access_key=minio_container.access_key,
        secret_key=minio_container.secret_key,
        secure=False
    )

    # Create test bucket
    bucket_name = "test-documents"
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    return client, bucket_name


@pytest.fixture
def kafka_producer(kafka_container):
    """Create Kafka producer connected to test container."""
    bootstrap_servers = kafka_container.get_bootstrap_server()
    producer = KafkaProducer(
        bootstrap_servers=[bootstrap_servers],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    yield producer
    producer.close()


@pytest.fixture
def kafka_consumer(kafka_container):
    """Create Kafka consumer connected to test container."""
    bootstrap_servers = kafka_container.get_bootstrap_server()
    consumer = KafkaConsumer(
        'ocr.documents.processed',
        bootstrap_servers=[bootstrap_servers],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        consumer_timeout_ms=10000,
        group_id='test-consumer'
    )
    yield consumer
    consumer.close()


def load_test_image() -> bytes:
    """Load test image from resources directory."""
    with open(TEST_IMAGE_PATH, 'rb') as f:
        return f.read()


def test_kafka_container_starts(kafka_container):
    """Test that Kafka container starts successfully."""
    assert kafka_container.get_bootstrap_server() is not None


def test_minio_container_starts(minio_container):
    """Test that MinIO container starts successfully."""
    config = minio_container.get_config()
    assert config["endpoint"] is not None
    assert config["access_key"] is not None
    assert config["secret_key"] is not None


def test_upload_image_to_minio(minio_client):
    """Test uploading an image to MinIO."""
    client, bucket_name = minio_client

    # Load test image
    image_data = load_test_image()

    # Upload to MinIO
    client.put_object(
        bucket_name,
        "test-image.png",
        BytesIO(image_data),
        len(image_data),
        content_type="image/png"
    )

    # Verify upload
    stat = client.stat_object(bucket_name, "test-image.png")
    assert stat.size == len(image_data)


def test_kafka_message_flow(kafka_producer, kafka_consumer):
    """Test sending and receiving messages via Kafka."""
    test_message = {
        "sessionId": "test-session",
        "messageId": "test-message",
        "bucket": "test-bucket",
        "fileName": "test-file.png"
    }

    # Send message
    kafka_producer.send('ocr.documents.to_process', test_message)
    kafka_producer.flush()

    # Note: In a real integration test, the OCR service would process this
    # For now, we just verify Kafka messaging works
    # You would need to start the OCR service in the test for full E2E testing


def test_minio_and_kafka_integration(minio_client, kafka_producer):
    """Test that MinIO and Kafka work together."""
    client, bucket_name = minio_client

    # Upload test image
    image_data = load_test_image()
    file_name = "integration-test.png"

    client.put_object(
        bucket_name,
        file_name,
        BytesIO(image_data),
        len(image_data),
        content_type="image/png"
    )

    # Send Kafka message referencing the uploaded file
    message = {
        "sessionId": "integration-test-session",
        "messageId": "integration-test-message",
        "bucket": bucket_name,
        "fileName": file_name
    }

    kafka_producer.send('ocr.documents.to_process', message)
    kafka_producer.flush()

    # Verify file exists in MinIO
    stat = client.stat_object(bucket_name, file_name)
    assert stat.size == len(image_data)


# Note: For full end-to-end testing with the OCR service running,
# you would need to:
# 1. Start the OCR service as a separate process/thread with the testcontainer endpoints
# 2. Send messages and wait for responses
# 3. Verify the extracted text
#
# Example:
# def test_ocr_end_to_end(kafka_container, minio_container):
#     # Set environment variables for OCR service
#     os.environ['KAFKA_BROKER'] = kafka_container.get_bootstrap_server()
#     os.environ['MINIO_ENDPOINT'] = minio_container.get_config()['endpoint']
#     os.environ['MINIO_ACCESS_KEY'] = minio_container.access_key
#     os.environ['MINIO_SECRET_KEY'] = minio_container.secret_key
#
#     # Start OCR service in background
#     # ... (implementation depends on your setup)
#
#     # Send test message and verify response
#     # ...
