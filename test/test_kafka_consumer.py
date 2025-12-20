"""Tests for Kafka consumer functionality."""

import pytest
import json
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestKafkaConsumer:
    """Test cases for Kafka consumer functionality."""

    def test_kafka_consumer_environment_variables(self):
        """Test that environment variables are properly loaded."""
        # Import here to test environment variable loading
        with patch.dict(os.environ, {
            'KAFKA_BROKER': 'test-broker:9092',
            'KAFKA_TOPIC_IN': 'test.topic.in',
            'KAFKA_TOPIC_OUT': 'test.topic.out',
            'KAFKA_GROUP_ID': 'test-group'
        }), patch.dict('sys.modules', {'paddleocr': Mock()}):
            import kafka_consumer
            # Re-import to pick up new env vars
            import importlib
            importlib.reload(kafka_consumer)
            
            assert kafka_consumer.KAFKA_BROKER == 'test-broker:9092'
            assert kafka_consumer.TOPIC_IN == 'test.topic.in'
            assert kafka_consumer.TOPIC_OUT == 'test.topic.out'
            assert kafka_consumer.GROUP_ID == 'test-group'

    def test_kafka_listener_successful_connection(self):
        """Test successful Kafka connection and message processing."""
        with patch.dict('sys.modules', {'paddleocr': Mock()}):
            import kafka_consumer
        
            # Mock message data
            test_payload = {
                "sessionId": "test-session-123",
                "messageId": "test-message-456",
                "bucket": "test-bucket",
                "fileName": "test-document.pdf"
            }
            
            # Mock Kafka message
            mock_message = Mock()
            mock_message.value = test_payload
            
            # Mock Kafka consumer and producer
            mock_consumer = Mock()
            # Mock the consumer to iterate once then raise StopIteration
            mock_consumer.__iter__ = Mock(return_value=iter([mock_message]))
            
            mock_producer = Mock()
            
            with patch('kafka_consumer.KafkaConsumer') as MockKafkaConsumer, \
                 patch('kafka_consumer.KafkaProducer') as MockKafkaProducer, \
                 patch('kafka_consumer.extract_text_from_s3') as mock_extract_text:
                
                MockKafkaConsumer.return_value = mock_consumer
                MockKafkaProducer.return_value = mock_producer
                mock_extract_text.return_value = "Extracted text content"

                # Call the listener (will return when iterator is exhausted)
                kafka_consumer.start_kafka_listener()

                # Verify OCR function was called
                mock_extract_text.assert_called_once_with("test-bucket", "test-document.pdf")
                
                # Verify producer was called with correct result
                expected_result = {
                    "sessionId": "test-session-123",
                    "messageId": "test-message-456",
                    "extractedText": "Extracted text content"
                }
                mock_producer.send.assert_called_once_with(kafka_consumer.TOPIC_OUT, expected_result)

    def test_kafka_listener_connection_retry(self):
        """Test Kafka connection retry mechanism."""
        with patch.dict('sys.modules', {'paddleocr': Mock()}):
            import kafka_consumer
        
            with patch('kafka_consumer.KafkaConsumer') as MockKafkaConsumer, \
                 patch('kafka_consumer.KafkaProducer') as MockKafkaProducer, \
                 patch('kafka_consumer.time.sleep') as mock_sleep:
                
                # Mock the consumer to return empty iterator to exit loop
                mock_consumer = Mock()
                mock_consumer.__iter__ = Mock(return_value=iter([]))
                
                # Mock connection failures for first 3 attempts, then success
                MockKafkaConsumer.side_effect = [
                    ConnectionError("Connection failed"),
                    ConnectionError("Connection failed"),
                    ConnectionError("Connection failed"),
                    mock_consumer  # Successful connection
                ]
                MockKafkaProducer.return_value = Mock()
                
                kafka_consumer.start_kafka_listener()
                
                # Verify retries occurred
                assert MockKafkaConsumer.call_count == 4
                assert mock_sleep.call_count == 3

    def test_kafka_listener_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        with patch.dict('sys.modules', {'paddleocr': Mock()}):
            import kafka_consumer
        
            with patch('kafka_consumer.KafkaConsumer') as MockKafkaConsumer, \
                 patch('kafka_consumer.time.sleep') as mock_sleep:
                
                # Mock connection failure for all attempts
                MockKafkaConsumer.side_effect = ConnectionError("Persistent connection error")

                with pytest.raises(ConnectionError, match="Kafka could not be reached after several attempts"):
                    kafka_consumer.start_kafka_listener()
                
                # Verify all retries were attempted
                assert MockKafkaConsumer.call_count == 25
                assert mock_sleep.call_count == 25

    def test_kafka_listener_message_processing_error(self, caplog):
        """Test handling of message processing errors."""
        with patch.dict('sys.modules', {'paddleocr': Mock()}):
            import kafka_consumer

            # Mock message with missing required fields
            test_payload = {
                "sessionId": "test-session-123",
                # Missing messageId, bucket, fileName
            }

            mock_message = Mock()
            mock_message.value = test_payload

            mock_consumer = Mock()
            mock_consumer.__iter__ = Mock(return_value=iter([mock_message]))

            mock_producer = Mock()

            with patch('kafka_consumer.KafkaConsumer') as MockKafkaConsumer, \
                 patch('kafka_consumer.KafkaProducer') as MockKafkaProducer:

                MockKafkaConsumer.return_value = mock_consumer
                MockKafkaProducer.return_value = mock_producer

                # Call the listener (will return when iterator is exhausted)
                kafka_consumer.start_kafka_listener()

                # Verify validation error was logged (Pydantic validation)
                assert any(
                    "Validation error" in record.message
                    for record in caplog.records
                )

    def test_kafka_listener_ocr_extraction_error(self, caplog):
        """Test handling of OCR extraction errors."""
        with patch.dict('sys.modules', {'paddleocr': Mock()}):
            import kafka_consumer

            test_payload = {
                "sessionId": "test-session-123",
                "messageId": "test-message-456",
                "bucket": "test-bucket",
                "fileName": "test-document.pdf"
            }

            mock_message = Mock()
            mock_message.value = test_payload

            mock_consumer = Mock()
            mock_consumer.__iter__ = Mock(return_value=iter([mock_message]))

            mock_producer = Mock()

            with patch('kafka_consumer.KafkaConsumer') as MockKafkaConsumer, \
                 patch('kafka_consumer.KafkaProducer') as MockKafkaProducer, \
                 patch('kafka_consumer.extract_text_from_s3') as mock_extract_text:

                MockKafkaConsumer.return_value = mock_consumer
                MockKafkaProducer.return_value = mock_producer
                mock_extract_text.side_effect = Exception("OCR processing failed")

                # Call the listener (will return when iterator is exhausted)
                kafka_consumer.start_kafka_listener()

                # Verify error was logged
                assert any(
                    "Unexpected error" in record.message
                    for record in caplog.records
                )