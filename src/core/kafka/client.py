"""Kafka client factory.

This module provides factories for creating Kafka consumers and producers
based on the configured Kafka provider (LOCAL, AZURE, etc.).
"""

import logging
import os
import json

from kafka import KafkaConsumer, KafkaProducer
from core.vault.client import SecretsVaultClientFactory


logger = logging.getLogger(__name__)

# Initialize secrets client for sensitive data
SECRETS_PROVIDER = os.getenv("SECRETS_PROVIDER", "LOCAL")
secrets_client = SecretsVaultClientFactory.create(type=SECRETS_PROVIDER)

# Get broker from secrets (sensitive data)
KAFKA_BROKER = secrets_client.get_secret("KAFKA_BROKER")

VALUE_SERIALIZER_LAMBDA = lambda v: json.dumps(v).encode('utf-8')


class KafkaConsumerFactory:
    """Factory class to create Kafka consumers based on the provider."""

    @staticmethod
    def create(
            topic: str,
            group_id: str,
            type: str = "LOCAL",
            session_timeout_ms: int = 10000
    ) -> KafkaConsumer:
        """Create and return a Kafka consumer based on the provider type.

        Args:
            topic: Kafka topic to subscribe to
            group_id: Consumer group ID
            type: The Kafka provider type. Supported values:
                  - LOCAL: Uses local Kafka
                  - AZURE: Uses Azure Event Hubs with SASL
            session_timeout_ms: Session timeout in milliseconds

        Returns:
            KafkaConsumer: Configured Kafka consumer instance

        Raises:
            ValueError: If an unsupported Kafka provider type is specified
        """
        config = {
            "bootstrap_servers": [KAFKA_BROKER],
            "group_id": group_id,
            "value_deserializer": lambda v: json.loads(v.decode("utf-8")),
            "session_timeout_ms": session_timeout_ms,
            "auto_offset_reset": "latest"
        }

        if type == "AZURE":
            logger.info("Creating Azure Event Hubs Kafka consumer")
            sasl_password = secrets_client.get_secret("KAFKA_SASL_PASSWORD")

            config.update({
                "security_protocol": "SASL_SSL",
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": "$ConnectionString",
                "sasl_plain_password": sasl_password,
                "enable_auto_commit": True,
            })
        elif type == "LOCAL":
            logger.info("Creating local Kafka consumer")
        else:
            raise ValueError(
                f"Unsupported Kafka provider type: {type}. "
                f"Supported types: LOCAL, AZURE"
            )

        return KafkaConsumer(topic, **config)


class KafkaProducerFactory:
    """Factory class to create Kafka producers based on the provider."""

    @staticmethod
    def create(type: str = "LOCAL") -> KafkaProducer:
        """Create and return a Kafka producer based on the provider type.

        Args:
            type: The Kafka provider type. Supported values:
                  - LOCAL: Uses local Kafka
                  - AZURE: Uses Azure Event Hubs with SASL

        Returns:
            KafkaProducer: Configured Kafka producer instance

        Raises:
            ValueError: If an unsupported Kafka provider type is specified
        """
        config = {
            "bootstrap_servers": [KAFKA_BROKER],
            "value_serializer": VALUE_SERIALIZER_LAMBDA,
        }

        if type == "AZURE":
            logger.info("Creating Azure Event Hubs Kafka producer")
            sasl_username = secrets_client.get_secret("KAFKA_SASL_USERNAME")
            sasl_password = secrets_client.get_secret("KAFKA_SASL_PASSWORD")

            config.update({
                "security_protocol": "SASL_SSL",
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": sasl_username,
                "sasl_plain_password": sasl_password,
                "max_block_ms": 60000,
            })
        elif type == "LOCAL":
            logger.info("Creating local Kafka producer")
            config.update({
                "max_block_ms": 10000,
            })
        else:
            raise ValueError(
                f"Unsupported Kafka provider type: {type}. "
                f"Supported types: LOCAL, AZURE"
            )

        return KafkaProducer(**config)
