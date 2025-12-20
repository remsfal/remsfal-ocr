"""Tests for Kafka message models."""

import pytest
from pydantic import ValidationError
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kafka_models import OcrInputMessage, OcrOutputMessage


class TestOcrInputMessage:
    """Test cases for OcrInputMessage model."""

    def test_valid_input_message(self):
        """Test creating a valid input message."""
        data = {
            "sessionId": "session-123",
            "messageId": "message-456",
            "bucket": "test-bucket",
            "fileName": "document.pdf"
        }
        msg = OcrInputMessage.model_validate(data)

        assert msg.sessionId == "session-123"
        assert msg.messageId == "message-456"
        assert msg.bucket == "test-bucket"
        assert msg.fileName == "document.pdf"

    def test_input_message_serialization(self):
        """Test serialization to dict."""
        msg = OcrInputMessage(
            sessionId="session-123",
            messageId="message-456",
            bucket="test-bucket",
            fileName="document.pdf"
        )

        data = msg.model_dump()
        assert data == {
            "sessionId": "session-123",
            "messageId": "message-456",
            "bucket": "test-bucket",
            "fileName": "document.pdf"
        }

    def test_input_message_missing_field(self):
        """Test validation error when required field is missing."""
        data = {
            "sessionId": "session-123",
            "bucket": "test-bucket",
            # Missing messageId and fileName
        }

        with pytest.raises(ValidationError) as exc_info:
            OcrInputMessage.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 2
        missing_fields = {error['loc'][0] for error in errors}
        assert missing_fields == {"messageId", "fileName"}

    def test_input_message_wrong_type(self):
        """Test validation error when field has wrong type."""
        data = {
            "sessionId": "session-123",
            "messageId": 123,  # Should be string
            "bucket": "test-bucket",
            "fileName": "document.pdf"
        }

        # Pydantic should raise validation error for wrong type
        with pytest.raises(ValidationError) as exc_info:
            OcrInputMessage.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]['loc'] == ('messageId',)
        assert errors[0]['type'] == 'string_type'


class TestOcrOutputMessage:
    """Test cases for OcrOutputMessage model."""

    def test_valid_output_message(self):
        """Test creating a valid output message."""
        data = {
            "sessionId": "session-123",
            "messageId": "message-456",
            "extractedText": "This is the extracted text"
        }
        msg = OcrOutputMessage.model_validate(data)

        assert msg.sessionId == "session-123"
        assert msg.messageId == "message-456"
        assert msg.extractedText == "This is the extracted text"

    def test_output_message_serialization(self):
        """Test serialization to dict."""
        msg = OcrOutputMessage(
            sessionId="session-123",
            messageId="message-456",
            extractedText="Extracted content"
        )

        data = msg.model_dump()
        assert data == {
            "sessionId": "session-123",
            "messageId": "message-456",
            "extractedText": "Extracted content"
        }

    def test_output_message_missing_field(self):
        """Test validation error when required field is missing."""
        data = {
            "sessionId": "session-123",
            # Missing messageId and extractedText
        }

        with pytest.raises(ValidationError) as exc_info:
            OcrOutputMessage.model_validate(data)

        errors = exc_info.value.errors()
        assert len(errors) == 2
        missing_fields = {error['loc'][0] for error in errors}
        assert missing_fields == {"messageId", "extractedText"}

    def test_output_message_empty_extracted_text(self):
        """Test that empty extracted text is valid."""
        msg = OcrOutputMessage(
            sessionId="session-123",
            messageId="message-456",
            extractedText=""
        )

        assert msg.extractedText == ""
