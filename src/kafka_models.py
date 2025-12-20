"""Pydantic models for Kafka message validation and serialization."""

from pydantic import BaseModel, Field


class OcrInputMessage(BaseModel):
    """Model for incoming OCR processing requests.

    Attributes:
        sessionId: Unique identifier for the session
        messageId: Unique identifier for the message
        bucket: S3 bucket name containing the document
        fileName: Name of the file to process in the bucket
    """
    sessionId: str = Field(..., description="Session identifier")
    messageId: str = Field(..., description="Message identifier")
    bucket: str = Field(..., description="S3 bucket name")
    fileName: str = Field(..., description="File name in the bucket")


class OcrOutputMessage(BaseModel):
    """Model for OCR processing results.

    Attributes:
        sessionId: Session identifier from the input message
        messageId: Message identifier from the input message
        extractedText: The text extracted from the document
    """
    sessionId: str = Field(..., description="Session identifier")
    messageId: str = Field(..., description="Message identifier")
    extractedText: str = Field(..., description="Extracted text content")
