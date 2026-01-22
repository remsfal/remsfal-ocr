"""Local environment secrets client implementation.

This module provides a local environment variable-based implementation
of the SecretsVaultClient interface.
"""

import logging
import os

from core.vault.base import SecretsVaultClient

logger = logging.getLogger(__name__)


class LocalEnvironmentClient(SecretsVaultClient):
    """Local environment implementation of the secrets vault client interface.
    
    Retrieves secrets from environment variables using os.getenv().
    """

    def __init__(self):
        """Initialize local environment secrets client."""
        logger.info("Local Environment secrets client initialized")

    def get_secret(self, name: str) -> str:
        """Retrieve a secret from environment variables.

        Args:
            name: Name of the environment variable

        Returns:
            str: The secret value from the environment variable

        Raises:
            ValueError: If the environment variable is not set
        """
        try:
            logger.info(f"Retrieving secret '{name}' from environment...")
            value = os.getenv(name)
            
            if value is None:
                raise ValueError(f"Environment variable '{name}' is not set")
            
            logger.info(f"Successfully retrieved secret '{name}'")
            return value
        except Exception as e:
            logger.error(f"Error retrieving secret from environment: {e}")
            raise
