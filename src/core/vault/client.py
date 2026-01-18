"""Secrets vault client factory.

This module provides a factory for creating secrets vault clients based on
the configured secrets provider (Local Environment, Azure Key Vault, etc.).
"""

import logging

from core.vault.base import SecretsVaultClient
from vault.local.client import LocalEnvironmentClient
from vault.keyvault.client import KeyVaultClient

logger = logging.getLogger(__name__)


class SecretsVaultClientFactory:
    """Factory class to create secrets vault clients based on the provider."""

    @staticmethod
    def create(type: str = "LOCAL") -> SecretsVaultClient:
        """Create and return a secrets vault client based on the provider type.

        Args:
            type: The secrets provider type. Supported values:
                  - LOCAL: Uses environment variables
                  - AZURE_KEYVAULT: Uses Azure Key Vault

        Returns:
            SecretsVaultClient: Configured secrets vault client instance

        Raises:
            ValueError: If an unsupported secrets provider type is specified
        """
        if type == "AZURE_KEYVAULT":
            logger.info("Creating Azure Key Vault client")
            return KeyVaultClient()
        elif type == "LOCAL":
            logger.info("Creating Local Environment secrets client")
            return LocalEnvironmentClient()
        else:
            raise ValueError(
                f"Unsupported secrets provider type: {type}. "
                f"Supported types: LOCAL, AZURE_KEYVAULT"
            )
