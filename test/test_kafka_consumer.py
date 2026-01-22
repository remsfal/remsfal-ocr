"""Tests for Kafka consumer functionality."""

import pytest
from pydantic import ValidationError
from unittest.mock import patch, Mock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def clear_kafka_modules():
    """Clear cached Kafka-related modules to allow fresh imports with mocks."""
    for mod in list(sys.modules.keys()):
        if any(x in mod for x in ['kafka', 'ocr', 'storage', 'vault', 'paddle']):
            del sys.modules[mod]


class TestKafkaConsumer:
    """Test cases for Kafka consumer functionality."""

    def test_kafka_consumer_environment_variables(self):
        """Test that environment variables are properly loaded."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'test-broker:9092',
            'KAFKA_TOPIC_IN': 'test.topic.in',
            'KAFKA_TOPIC_OUT': 'test.topic.out',
            'KAFKA_GROUP_ID': 'test-group',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            # Mock PaddleOCR and storage
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
                    import kafka_consumer
                    
                    assert kafka_consumer.TOPIC_IN == 'test.topic.in'
                    assert kafka_consumer.TOPIC_OUT == 'test.topic.out'
                    assert kafka_consumer.GROUP_ID == 'test-group'

    def test_kafka_listener_successful_connection(self):
        """Test successful Kafka connection and message processing."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
                    # Mock message data
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
                    
                    # Patch at the location where they're used (kafka_consumer module)
                    with patch('kafka_consumer.KafkaConsumerFactory') as MockConsumerFactory, \
                         patch('kafka_consumer.KafkaProducerFactory') as MockProducerFactory, \
                         patch('kafka_consumer.extract_text_from_s3') as mock_extract_text:
                        
                        MockConsumerFactory.create.return_value = mock_consumer
                        MockProducerFactory.create.return_value = mock_producer
                        mock_extract_text.return_value = "Extracted text content"
                        
                        import kafka_consumer
                        kafka_consumer.start_kafka_listener()
                        
                        mock_extract_text.assert_called_once_with("test-bucket", "test-document.pdf")
                        
                        expected_result = {
                            "sessionId": "test-session-123",
                            "messageId": "test-message-456",
                            "extractedText": "Extracted text content"
                        }
                        mock_producer.send.assert_called_once_with(
                            kafka_consumer.TOPIC_OUT, 
                            expected_result
                        )

    def test_kafka_listener_connection_retry(self):
        """Test Kafka connection retry mechanism."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
                    mock_consumer = Mock()
                    mock_consumer.__iter__ = Mock(return_value=iter([]))
                    
                    with patch('kafka_consumer.KafkaConsumerFactory') as MockConsumerFactory, \
                         patch('kafka_consumer.KafkaProducerFactory') as MockProducerFactory, \
                         patch('kafka_consumer.time.sleep') as mock_sleep:
                        
                        # Mock connection failures for first 3 attempts, then success
                        MockConsumerFactory.create.side_effect = [
                            ConnectionError("Connection failed"),
                            ConnectionError("Connection failed"),
                            ConnectionError("Connection failed"),
                            mock_consumer
                        ]
                        MockProducerFactory.create.return_value = Mock()
                        
                        import kafka_consumer
                        kafka_consumer.start_kafka_listener()
                        
                        assert MockConsumerFactory.create.call_count == 4
                        assert mock_sleep.call_count == 3

    def test_kafka_listener_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
                    with patch('kafka_consumer.KafkaConsumerFactory') as MockConsumerFactory, \
                         patch('kafka_consumer.time.sleep') as mock_sleep:
                        
                        MockConsumerFactory.create.side_effect = ConnectionError("Persistent connection error")
                        
                        import kafka_consumer
                        
                        with pytest.raises(ConnectionError, match="Kafka could not be reached after several attempts"):
                            kafka_consumer.start_kafka_listener()
                        
                        assert MockConsumerFactory.create.call_count == 25
                        assert mock_sleep.call_count == 25

    def test_kafka_listener_message_processing_error(self, caplog):
        """Test handling of message processing errors."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
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
                    
                    with patch('kafka_consumer.KafkaConsumerFactory') as MockConsumerFactory, \
                         patch('kafka_consumer.KafkaProducerFactory') as MockProducerFactory:
                        
                        MockConsumerFactory.create.return_value = mock_consumer
                        MockProducerFactory.create.return_value = mock_producer
                        
                        import kafka_consumer
                        kafka_consumer.start_kafka_listener()
                        
                        # Verify validation error was logged
                        assert any(
                            "Validation error" in record.message
                            for record in caplog.records
                        )

    def test_kafka_listener_ocr_extraction_error(self, caplog):
        """Test handling of OCR extraction errors."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
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
                    
                    with patch('kafka_consumer.KafkaConsumerFactory') as MockConsumerFactory, \
                         patch('kafka_consumer.KafkaProducerFactory') as MockProducerFactory, \
                         patch('kafka_consumer.extract_text_from_s3') as mock_extract_text:
                        
                        MockConsumerFactory.create.return_value = mock_consumer
                        MockProducerFactory.create.return_value = mock_producer
                        mock_extract_text.side_effect = Exception("OCR processing failed")
                        
                        import kafka_consumer
                        kafka_consumer.start_kafka_listener()
                        
                        assert any(
                            "Unexpected error" in record.message
                            for record in caplog.records
                        )


class TestProcessMessage:
    """Test cases for process_message function."""

    def test_process_message_success(self):
        """Test successful message processing."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
                    test_payload = {
                        "sessionId": "session-123",
                        "messageId": "message-456",
                        "bucket": "my-bucket",
                        "fileName": "document.png"
                    }
                    
                    mock_message = Mock()
                    mock_message.value = test_payload
                    
                    mock_producer = Mock()
                    
                    with patch('kafka_consumer.extract_text_from_s3') as mock_extract:
                        mock_extract.return_value = "Extracted OCR text"
                        
                        import kafka_consumer
                        kafka_consumer.process_message(mock_message, mock_producer)
                        
                        mock_extract.assert_called_once_with("my-bucket", "document.png")
                        mock_producer.send.assert_called_once()
                        
                        call_args = mock_producer.send.call_args
                        assert call_args[0][0] == kafka_consumer.TOPIC_OUT
                        result = call_args[0][1]
                        assert result["sessionId"] == "session-123"
                        assert result["messageId"] == "message-456"
                        assert result["extractedText"] == "Extracted OCR text"

    def test_process_message_validation_error(self):
        """Test that invalid messages raise ValidationError."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092',
            'STORAGE_PROVIDER': 'LOCAL',
            'MINIO_ENDPOINT': 'localhost:9000',
            'MINIO_ACCESS_KEY': 'test',
            'MINIO_SECRET_KEY': 'test'
        }):
            clear_kafka_modules()
            
            mock_paddle = Mock()
            mock_paddle.PaddleOCR.return_value = Mock()
            
            with patch.dict('sys.modules', {'paddleocr': mock_paddle}):
                with patch('core.storage.client.StorageClientFactory') as MockStorageFactory:
                    MockStorageFactory.create.return_value = Mock()
                    
                    import kafka_consumer
                    
                    # Message with missing required fields
                    invalid_payload = {
                        "sessionId": "session-123"
                        # Missing messageId, bucket, fileName
                    }
                    
                    mock_message = Mock()
                    mock_message.value = invalid_payload
                    mock_producer = Mock()
                    
                    with pytest.raises(ValidationError):
                        kafka_consumer.process_message(mock_message, mock_producer)
