"""Main entry point for the REMSFAL OCR microservice.

This module starts the OCR microservice which listens for document processing
requests via Kafka, performs OCR text extraction, and publishes results.
"""

# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

import logging
import sys
from kafka_consumer import start_kafka_listener

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
    force=True
)

# Suppress DEBUG messages from PaddleOCR
logging.getLogger('ppocr').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting OCR microservice...")
    start_kafka_listener()
