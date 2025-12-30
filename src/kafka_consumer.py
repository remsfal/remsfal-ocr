"""Kafka consumer for OCR document processing.

This module implements a resilient Kafka consumer that:
- Listens for OCR processing requests from a Kafka topic
- Validates incoming messages using Pydantic models
- Extracts text from documents stored in S3
- Publishes results to an output Kafka topic
- Automatically reconnects with exponential backoff on failures
"""

import json
import logging
import os
import time
from dotenv import load_dotenv
from kafka.errors import KafkaError
from pydantic import ValidationError
from ocr_engine import extract_text_from_s3
from kafka_models import OcrInputMessage, OcrOutputMessage
from core.kafka.client import KafkaConsumerFactory, KafkaProducerFactory

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Get configuration from environment (not secrets)
TOPIC_IN = os.getenv("KAFKA_TOPIC_IN", "ocr.documents.to_process")
TOPIC_OUT = os.getenv("KAFKA_TOPIC_OUT", "ocr.documents.processed")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "ocr-service")
KAFKA_PROVIDER = os.getenv("KAFKA_PROVIDER", "LOCAL")


def process_message(message, producer):
    """Process a single Kafka message and publish the result.

    This function:
    1. Validates the incoming message using Pydantic
    2. Extracts text from the document stored in S3
    3. Creates an output message with the extracted text
    4. Publishes the result to the output Kafka topic

    Args:
        message: Kafka message containing the OCR request
        producer: KafkaProducer instance for publishing results

    Raises:
        ValidationError: If the input message schema is invalid
        IOError/OSError: If S3 download or file operations fail
        Exception: For any other unexpected errors during processing
    """
    payload = message.value
    logger.info(f"Received: {payload}")

    # Validate and parse input message with Pydantic
    input_msg = OcrInputMessage.model_validate(payload)

    # Extract text from S3
    extracted_text = extract_text_from_s3(input_msg.bucket, input_msg.fileName)

    # Create and validate output message
    output_msg = OcrOutputMessage(
        sessionId=input_msg.sessionId,
        messageId=input_msg.messageId,
        extractedText=extracted_text
    )

    # Serialize to dict for Kafka (camelCase keys)
    result = output_msg.model_dump(by_alias=True)

    producer.send(TOPIC_OUT, result)
    logger.info(f"Published result to '{TOPIC_OUT}': {result}")


def start_kafka_listener():
    """Start the Kafka consumer with self-healing capabilities.

    This function establishes a connection to Kafka and processes OCR requests.
    It implements a resilient architecture with:
    - Automatic reconnection with exponential backoff (5s to 5min)
    - Specific exception handling for different error types
    - Graceful shutdown on KeyboardInterrupt (Ctrl-C)

    The consumer processes messages in a loop:
    1. Validates incoming messages using Pydantic
    2. Downloads documents from S3
    3. Performs OCR text extraction
    4. Publishes results to output topic

    Error handling strategy:
    - ValidationError: Skip invalid messages
    - IOError/OSError: Skip messages with S3/file errors
    - KafkaError: Reconnect with exponential backoff
    - Exception: Log unexpected errors and skip message

    Raises:
        ConnectionError: If Kafka is unreachable after max retries (25 attempts)

    Returns:
        None: Function runs indefinitely until interrupted or unrecoverable error
    """
    max_retries = 25
    initial_delay = 5  # seconds
    max_delay = 300  # 5 minutes maximum backoff

    while True:  # Outer loop for reconnect with self-healing
        retry_delay = initial_delay

        # Try to establish Kafka connection with exponential backoff
        for attempt in range(max_retries):
            try:
                consumer = KafkaConsumerFactory.create(
                    topic=TOPIC_IN,
                    group_id=GROUP_ID,
                    type=KAFKA_PROVIDER,
                    session_timeout_ms=30000,
                )
                producer = KafkaProducerFactory.create(type=KAFKA_PROVIDER)
                logger.info(f"Listening to topic '{TOPIC_IN}'...")
                retry_delay = initial_delay  # Reset delay on successful connection
                break
            except (KafkaError, ConnectionError) as e:
                logger.warning(f"Kafka not reachable, retrying in {retry_delay}s... ({attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff with cap
        else:
            raise ConnectionError("Kafka could not be reached after several attempts")

        # Process messages with specific exception handling
        try:
            for message in consumer:
                try:
                    process_message(message, producer)
                except ValidationError as e:
                    logger.error(f"Validation error - skipping message: {e}")
                except (IOError, OSError) as e:
                    logger.error(f"S3/File error - skipping message: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error processing message - skipping: {e}")

            # If we reach here, the consumer iterator ended (only happens in tests)
            return

        except (StopIteration, KeyboardInterrupt):
            # Allow graceful shutdown (Ctrl-C) and test termination
            logger.info("Shutting down gracefully...")
            return  # Exit the function completely
        except KafkaError as e:
            logger.error(f"Kafka connection lost: {e}. Reconnecting with exponential backoff...")
            continue  # Restart connection loop
