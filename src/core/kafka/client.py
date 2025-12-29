import os
import json

from kafka import KafkaConsumer, KafkaProducer


KAFKA_PROVIDER = os.getenv("KAFKA_PROVIDER", "LOCAL")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")

VALUE_SERIALIZER_LAMBDA = lambda v: json.dumps(v).encode('utf-8')


class KafkaConsumerFactory:
    """Factory class to create Kafka clients based on the provider."""

    @staticmethod
    def create(
            topic: str,
            group_id: str,
            session_timeout_ms: int = 10000
    ) -> KafkaConsumer:
        """Create and return a Kafka consumer based on the provider.

        Args:
            topic: Kafka topic to subscribe to
            group_id: Consumer group ID
            session_timeout_ms: Session timeout in milliseconds
        Returns:
            KafkaConsumer: Configured Kafka consumer instance
        """
        config = {
            "bootstrap_servers": [KAFKA_BROKER],
            "group_id": group_id,
            "value_deserializer": lambda v: json.loads(v.decode("utf-8")),
            "session_timeout_ms": session_timeout_ms,
            "auto_offset_reset": "latest"
        }

        if KAFKA_PROVIDER == "AZURE":
            config.update({
                "security_protocol": "SASL_SSL",
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": os.getenv("KAFKA_SASL_USERNAME"),
                "sasl_plain_password": os.getenv("KAFKA_SASL_PASSWORD"),
                "enable_auto_commit": True,
            })
        elif KAFKA_PROVIDER == "LOCAL":
            config.update({

            })

        return KafkaConsumer(topic, **config)


class KafkaProducerFactory:
    """Factory class to create Kafka producers based on the provider."""

    @staticmethod
    def create() -> KafkaProducer:
        """Create and return a Kafka producer based on the provider.

        Returns:
            KafkaProducer: Configured Kafka producer instance
        """
        config = {
            "bootstrap_servers": [KAFKA_BROKER],
            "value_serializer": VALUE_SERIALIZER_LAMBDA,
        }

        if KAFKA_PROVIDER == "AZURE":
            config.update({
                "security_protocol": "SASL_SSL",
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": os.getenv("KAFKA_SASL_USERNAME"),
                "sasl_plain_password": os.getenv("KAFKA_SASL_PASSWORD"),
                "max_block_ms": 60000,
            })
        elif KAFKA_PROVIDER == "LOCAL":
            config.update({
                "max_block_ms": 10000,
            })

        return KafkaProducer(**config)
