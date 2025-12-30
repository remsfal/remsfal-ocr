"""Tests for vault client functionality using Factory Pattern."""

import pytest
from unittest.mock import patch, Mock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSecretsVaultClientFactory:
    """Test cases for SecretsVaultClientFactory."""

    def test_factory_create_local_client(self):
        """Test factory creates LocalEnvironmentClient for LOCAL type."""
        # Clear cached modules
        for mod in list(sys.modules.keys()):
            if 'vault' in mod:
                del sys.modules[mod]
        
        from core.vault.client import SecretsVaultClientFactory
        from vault.local.client import LocalEnvironmentClient
        
        client = SecretsVaultClientFactory.create(type="LOCAL")
        
        assert isinstance(client, LocalEnvironmentClient)

    def test_factory_create_keyvault_client(self):
        """Test factory creates KeyVaultClient for AZURE_KEYVAULT type."""
        with patch.dict(os.environ, {
            'KEYVAULT_URL': 'https://testvault.vault.azure.net',
            'KEYVAULT_AUTH_METHOD': 'MANAGED_IDENTITY'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('azure.identity.DefaultAzureCredential') as MockCredential:
                with patch('azure.keyvault.secrets.SecretClient') as MockSecretClient:
                    MockCredential.return_value = Mock()
                    MockSecretClient.return_value = Mock()
                    
                    from core.vault.client import SecretsVaultClientFactory
                    from vault.keyvault.client import KeyVaultClient
                    
                    client = SecretsVaultClientFactory.create(type="AZURE_KEYVAULT")
                    
                    assert isinstance(client, KeyVaultClient)

    def test_factory_invalid_type_raises_error(self):
        """Test factory raises ValueError for unsupported type."""
        # Clear cached modules
        for mod in list(sys.modules.keys()):
            if 'vault' in mod:
                del sys.modules[mod]
        
        from core.vault.client import SecretsVaultClientFactory
        
        with pytest.raises(ValueError, match="Unsupported secrets provider type"):
            SecretsVaultClientFactory.create(type="INVALID_TYPE")

    def test_factory_default_type_is_local(self):
        """Test factory defaults to LOCAL type."""
        # Clear cached modules
        for mod in list(sys.modules.keys()):
            if 'vault' in mod:
                del sys.modules[mod]
        
        from core.vault.client import SecretsVaultClientFactory
        from vault.local.client import LocalEnvironmentClient
        
        client = SecretsVaultClientFactory.create()  # No type specified
        
        assert isinstance(client, LocalEnvironmentClient)


class TestLocalEnvironmentClient:
    """Test cases for LocalEnvironmentClient."""

    def test_get_secret_success(self):
        """Test successful secret retrieval from environment."""
        with patch.dict(os.environ, {
            'TEST_SECRET': 'my-secret-value'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            from vault.local.client import LocalEnvironmentClient
            
            client = LocalEnvironmentClient()
            result = client.get_secret('TEST_SECRET')
            
            assert result == 'my-secret-value'

    def test_get_secret_not_found_raises_error(self):
        """Test that missing secret raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure the secret doesn't exist
            if 'NONEXISTENT_SECRET' in os.environ:
                del os.environ['NONEXISTENT_SECRET']
            
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            from vault.local.client import LocalEnvironmentClient
            
            client = LocalEnvironmentClient()
            
            with pytest.raises(ValueError, match="Environment variable 'NONEXISTENT_SECRET' is not set"):
                client.get_secret('NONEXISTENT_SECRET')

    def test_get_secret_empty_value(self):
        """Test that empty secret value is valid."""
        with patch.dict(os.environ, {
            'EMPTY_SECRET': ''
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            from vault.local.client import LocalEnvironmentClient
            
            client = LocalEnvironmentClient()
            result = client.get_secret('EMPTY_SECRET')
            
            assert result == ''

    def test_get_multiple_secrets(self):
        """Test retrieving multiple secrets."""
        with patch.dict(os.environ, {
            'SECRET_ONE': 'value-one',
            'SECRET_TWO': 'value-two',
            'SECRET_THREE': 'value-three'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            from vault.local.client import LocalEnvironmentClient
            
            client = LocalEnvironmentClient()
            
            assert client.get_secret('SECRET_ONE') == 'value-one'
            assert client.get_secret('SECRET_TWO') == 'value-two'
            assert client.get_secret('SECRET_THREE') == 'value-three'


class TestKeyVaultClient:
    """Test cases for KeyVaultClient."""

    def test_client_initialization(self):
        """Test KeyVaultClient initializes with correct vault URL."""
        with patch.dict(os.environ, {
            'KEYVAULT_URL': 'https://myvault.vault.azure.net',
            'KEYVAULT_AUTH_METHOD': 'MANAGED_IDENTITY'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('azure.identity.DefaultAzureCredential') as MockCredential:
                with patch('azure.keyvault.secrets.SecretClient') as MockSecretClient:
                    mock_credential = Mock()
                    MockCredential.return_value = mock_credential
                    MockSecretClient.return_value = Mock()
                    
                    from vault.keyvault.client import KeyVaultClient
                    
                    client = KeyVaultClient()
                    
                    MockSecretClient.assert_called_once_with(
                        vault_url='https://myvault.vault.azure.net',
                        credential=mock_credential
                    )

    def test_get_secret_success(self):
        """Test successful secret retrieval from Key Vault."""
        with patch.dict(os.environ, {
            'KEYVAULT_URL': 'https://myvault.vault.azure.net',
            'KEYVAULT_AUTH_METHOD': 'MANAGED_IDENTITY'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('azure.identity.DefaultAzureCredential'):
                with patch('azure.keyvault.secrets.SecretClient') as MockSecretClient:
                    mock_secret = Mock()
                    mock_secret.value = 'secret-from-keyvault'
                    
                    mock_client = Mock()
                    mock_client.get_secret.return_value = mock_secret
                    MockSecretClient.return_value = mock_client
                    
                    from vault.keyvault.client import KeyVaultClient
                    
                    client = KeyVaultClient()
                    result = client.get_secret('MY_SECRET')
                    
                    # KeyVault uses hyphens instead of underscores
                    mock_client.get_secret.assert_called_once()
                    assert result == 'secret-from-keyvault'

    def test_get_secret_error(self):
        """Test handling of Key Vault errors."""
        with patch.dict(os.environ, {
            'KEYVAULT_URL': 'https://myvault.vault.azure.net',
            'KEYVAULT_AUTH_METHOD': 'MANAGED_IDENTITY'
        }):
            # Clear cached modules
            for mod in list(sys.modules.keys()):
                if 'vault' in mod:
                    del sys.modules[mod]
            
            with patch('azure.identity.DefaultAzureCredential'):
                with patch('azure.keyvault.secrets.SecretClient') as MockSecretClient:
                    mock_client = Mock()
                    mock_client.get_secret.side_effect = Exception("Key Vault error")
                    MockSecretClient.return_value = mock_client
                    
                    from vault.keyvault.client import KeyVaultClient
                    
                    client = KeyVaultClient()
                    
                    with pytest.raises(Exception, match="Key Vault error"):
                        client.get_secret('MY_SECRET')
