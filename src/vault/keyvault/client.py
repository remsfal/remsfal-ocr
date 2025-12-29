"""Azure Key Vault secrets client implementation.

This module provides an Azure Key Vault-specific implementation
of the SecretsVaultClient interface.
"""

import logging
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential

from core.vault.base import SecretsVaultClient

logger = logging.getLogger(__name__)


KEYVAULT_SECRETS_MAPPING = {
    "STORAGE_CONNECTION_STRING": "storage-connection-string",
    "KAFKA_SASL_PASSWORD": "eventhub-sasl-password",
    "KAFKA_BROKER": "eventhub-bootstrap-server",
    "KAFKA_SASL_USERNAME": "eventhub-sasl-username"
}


class KeyVaultClient(SecretsVaultClient):
    """Azure Key Vault implementation of the secrets vault client interface.
    
    Retrieves secrets from Azure Key Vault using either:
    - Managed Identity (DefaultAzureCredential)
    - Service Principal (ClientSecretCredential) with client ID and secret
    """

    def __init__(self):
        """Initialize Azure Key Vault client.
        
        Authentication is determined by KEYVAULT_AUTH_METHOD environment variable:
        - 'MANAGED_IDENTITY' (default): Uses DefaultAzureCredential
        - 'SERVICE_PRINCIPAL': Uses ClientSecretCredential with AZURE_CLIENT_ID, 
          AZURE_CLIENT_SECRET, and AZURE_TENANT_ID
        """
        self.vault_url = os.getenv("KEYVAULT_URL")
        if not self.vault_url:
            raise ValueError("KEYVAULT_URL environment variable is required for Azure Key Vault")
        
        auth_method = os.getenv("KEYVAULT_AUTH_METHOD", "MANAGED_IDENTITY")
        
        if auth_method == "SERVICE_PRINCIPAL":
            # Use Service Principal authentication
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")
            tenant_id = os.getenv("AZURE_TENANT_ID")
            
            if not all([client_id, client_secret, tenant_id]):
                raise ValueError(
                    "AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID "
                    "are required for SERVICE_PRINCIPAL authentication"
                )
            
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
            logger.info(f"Azure Key Vault client initialized with Service Principal auth: {self.vault_url}")
        else:
            # Use Managed Identity (DefaultAzureCredential)
            credential = DefaultAzureCredential()
            logger.info(f"Azure Key Vault client initialized with Managed Identity: {self.vault_url}")
        
        self.client = SecretClient(vault_url=self.vault_url, credential=credential)

    def get_secret(self, name: str) -> str:
        """Retrieve a secret from Azure Key Vault.

        Args:
            name: Name of the secret in Key Vault

        Returns:
            str: The secret value

        Raises:
            Exception: If the secret cannot be retrieved (not found, permission errors, etc.)
        """
        name = self._get_secret_name(name)
        try:
            logger.info(f"Retrieving secret '{name}' from Azure Key Vault...")
            secret = self.client.get_secret(name)
            logger.info(f"Successfully retrieved secret '{name}'")
            return secret.value
        except Exception as e:
            logger.error(f"Error retrieving secret from Azure Key Vault: {e}")
            raise
    
    def _get_secret_name(self, name: str) -> str:
        """Helper to format secret name if needed.
        
        Currently a no-op, but can be extended for naming conventions.
        """
        return KEYVAULT_SECRETS_MAPPING.get(name, name)
