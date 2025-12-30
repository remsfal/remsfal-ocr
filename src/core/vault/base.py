"""Base interface for secrets vault clients.

This module defines the abstract base class for secrets management operations,
providing a common interface for different secret providers (Environment, Azure Key Vault, etc.).
"""

from abc import ABC, abstractmethod


class SecretsVaultClient(ABC):
    """Abstract base class for secrets vault client implementations.
    
    This interface defines the contract that all secrets providers
    (Local Environment, Azure Key Vault, etc.) must implement.
    """

    @abstractmethod
    def get_secret(self, name: str) -> str:
        """Retrieve a secret by name.

        Args:
            name: Name of the secret to retrieve

        Returns:
            str: The secret value

        Raises:
            Exception: If the secret cannot be retrieved
        """
        pass
