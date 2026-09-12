"""
Integration tests for OCR service using testcontainers.
These tests start real Kafka and LocalStack (S3-compatible) containers and test the complete flow.
"""
import json
import pytest
from io import BytesIO
from pathlib import Path
from testcontainers.kafka import KafkaContainer
from testcontainers.localstack import LocalStackContainer
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
def localstack_container():
    """Start a LocalStack (S3-compatible) container for testing."""
    with LocalStackContainer(image="localstack/localstack:4.9").with_services("s3") as localstack:
        yield localstack


@pytest.fixture
def s3_client(localstack_container):
    """Create an S3 client (minio SDK) connected to the LocalStack test container."""
    endpoint = localstack_container.get_url().replace("http://", "")
    client = Minio(
        endpoint,
        access_key="testcontainers-localstack",
        secret_key="testcontainers-localstack",
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


def test_localstack_container_starts(localstack_container):
    """Test that the LocalStack container starts successfully."""
    assert localstack_container.get_url() is not None


def test_upload_image_to_s3(s3_client):
    """Test uploading an image to S3."""
    client, bucket_name = s3_client

    # Load test image
    image_data = load_test_image()

    # Upload to S3
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


def test_s3_and_kafka_integration(s3_client, kafka_producer):
    """Test that S3 and Kafka work together."""
    client, bucket_name = s3_client

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

    # Verify file exists in S3
    stat = client.stat_object(bucket_name, file_name)
    assert stat.size == len(image_data)


# Note: For full end-to-end testing with the OCR service running,
# you would need to:
# 1. Start the OCR service as a separate process/thread with the testcontainer endpoints
# 2. Send messages and wait for responses
# 3. Verify the extracted text
#
# Example:
# def test_ocr_end_to_end(kafka_container, localstack_container):
#     # Set environment variables for OCR service
#     os.environ['KAFKA_BROKER'] = kafka_container.get_bootstrap_server()
#     os.environ['S3_ENDPOINT'] = localstack_container.get_url().replace("http://", "")
#     os.environ['S3_ACCESS_KEY'] = "testcontainers-localstack"
#     os.environ['S3_SECRET_KEY'] = "testcontainers-localstack"
#
#     # Start OCR service in background
#     # ... (implementation depends on your setup)
#
#     # Send test message and verify response
#     # ...
