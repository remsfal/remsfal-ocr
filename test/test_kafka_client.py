"""Tests for Kafka client functionality using Factory Pattern."""

import pytest
from unittest.mock import patch, Mock, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestKafkaConsumerFactory:
    """Test cases for KafkaConsumerFactory."""

    def test_create_local_consumer(self):
        """Test factory creates consumer for LOCAL provider."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaConsumer') as MockKafkaConsumer:
                mock_consumer = Mock()
                MockKafkaConsumer.return_value = mock_consumer
                
                from core.kafka.client import KafkaConsumerFactory
                
                consumer = KafkaConsumerFactory.create(
                    topic='test-topic',
                    group_id='test-group',
                    session_timeout_ms=10000
                )
                
                assert consumer == mock_consumer
                MockKafkaConsumer.assert_called_once()
                call_kwargs = MockKafkaConsumer.call_args[1]
                assert call_kwargs['bootstrap_servers'] == ['localhost:9092']
                assert call_kwargs['group_id'] == 'test-group'
                assert call_kwargs['session_timeout_ms'] == 10000

    def test_create_azure_consumer(self):
        """Test factory creates consumer with SASL for AZURE provider."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'AZURE',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'mynamespace.servicebus.windows.net:9093',
            'KAFKA_SASL_PASSWORD': 'connection-string-password'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaConsumer') as MockKafkaConsumer:
                mock_consumer = Mock()
                MockKafkaConsumer.return_value = mock_consumer
                
                from core.kafka.client import KafkaConsumerFactory
                
                consumer = KafkaConsumerFactory.create(
                    topic='test-topic',
                    group_id='test-group'
                )
                
                assert consumer == mock_consumer
                call_kwargs = MockKafkaConsumer.call_args[1]
                assert call_kwargs['security_protocol'] == 'SASL_SSL'
                assert call_kwargs['sasl_mechanism'] == 'PLAIN'
                assert call_kwargs['sasl_plain_username'] == '$ConnectionString'
                assert call_kwargs['sasl_plain_password'] == 'connection-string-password'

    def test_consumer_with_default_timeout(self):
        """Test consumer factory uses default session timeout."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaConsumer') as MockKafkaConsumer:
                MockKafkaConsumer.return_value = Mock()
                
                from core.kafka.client import KafkaConsumerFactory
                
                KafkaConsumerFactory.create(
                    topic='test-topic',
                    group_id='test-group'
                )
                
                call_kwargs = MockKafkaConsumer.call_args[1]
                assert call_kwargs['session_timeout_ms'] == 10000  # default value


class TestKafkaProducerFactory:
    """Test cases for KafkaProducerFactory."""

    def test_create_local_producer(self):
        """Test factory creates producer for LOCAL provider."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaProducer') as MockKafkaProducer:
                mock_producer = Mock()
                MockKafkaProducer.return_value = mock_producer
                
                from core.kafka.client import KafkaProducerFactory
                
                producer = KafkaProducerFactory.create()
                
                assert producer == mock_producer
                MockKafkaProducer.assert_called_once()
                call_kwargs = MockKafkaProducer.call_args[1]
                assert call_kwargs['bootstrap_servers'] == ['localhost:9092']
                assert call_kwargs['max_block_ms'] == 10000

    def test_create_azure_producer(self):
        """Test factory creates producer with SASL for AZURE provider."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'AZURE',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'mynamespace.servicebus.windows.net:9093',
            'KAFKA_SASL_USERNAME': '$ConnectionString',
            'KAFKA_SASL_PASSWORD': 'connection-string-password'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaProducer') as MockKafkaProducer:
                mock_producer = Mock()
                MockKafkaProducer.return_value = mock_producer
                
                from core.kafka.client import KafkaProducerFactory
                
                producer = KafkaProducerFactory.create()
                
                assert producer == mock_producer
                call_kwargs = MockKafkaProducer.call_args[1]
                assert call_kwargs['security_protocol'] == 'SASL_SSL'
                assert call_kwargs['sasl_mechanism'] == 'PLAIN'
                assert call_kwargs['max_block_ms'] == 60000

    def test_producer_value_serializer(self):
        """Test producer has correct value serializer."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'localhost:9092'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaProducer') as MockKafkaProducer:
                MockKafkaProducer.return_value = Mock()
                
                from core.kafka.client import KafkaProducerFactory
                
                KafkaProducerFactory.create()
                
                call_kwargs = MockKafkaProducer.call_args[1]
                # Test the serializer function
                serializer = call_kwargs['value_serializer']
                test_dict = {"key": "value"}
                result = serializer(test_dict)
                assert result == b'{"key": "value"}'


class TestKafkaClientIntegration:
    """Integration tests for Kafka client factories."""

    def test_consumer_and_producer_same_broker(self):
        """Test consumer and producer use the same broker configuration."""
        with patch.dict(os.environ, {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL',
            'KAFKA_BROKER': 'shared-broker:9092'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('core.kafka.client.KafkaConsumer') as MockConsumer, \
                 patch('core.kafka.client.KafkaProducer') as MockProducer:
                
                MockConsumer.return_value = Mock()
                MockProducer.return_value = Mock()
                
                from core.kafka.client import KafkaConsumerFactory, KafkaProducerFactory
                
                KafkaConsumerFactory.create(topic='test', group_id='group')
                KafkaProducerFactory.create()
                
                consumer_broker = MockConsumer.call_args[1]['bootstrap_servers']
                producer_broker = MockProducer.call_args[1]['bootstrap_servers']
                
                assert consumer_broker == producer_broker == ['shared-broker:9092']

    def test_missing_broker_secret_raises_error(self):
        """Test that missing KAFKA_BROKER raises error."""
        # Clear the KAFKA_BROKER env var
        env_without_broker = {
            'KAFKA_PROVIDER': 'LOCAL',
            'SECRETS_PROVIDER': 'LOCAL'
        }
        
        with patch.dict(os.environ, env_without_broker, clear=True):
            # Ensure KAFKA_BROKER is not set
            if 'KAFKA_BROKER' in os.environ:
                del os.environ['KAFKA_BROKER']
            
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'kafka' in mod.lower() or 'vault' in mod:
                    del sys.modules[mod]
            
            with pytest.raises(ValueError, match="KAFKA_BROKER"):
                from core.kafka.client import KafkaConsumerFactory
