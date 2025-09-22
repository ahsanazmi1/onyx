"""
Trust Registry v0 implementation for Onyx.

Provides allowlist functionality for credential providers.
"""

import os

import yaml


class TrustRegistry:
    """
    Trust Registry v0 - Allowlist of Credential Providers.

    Manages a list of trusted credential providers that are allowed
    to participate in the Open Checkout Network (OCN) ecosystem.
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize the Trust Registry.

        Args:
            config_path: Optional path to trust registry YAML config.
                        If None, uses built-in fallback allowlist.
        """
        self.config_path = config_path
        self._providers: set[str] = set()
        self._load_allowlist()

    def _load_allowlist(self) -> None:
        """Load the allowlist from config file or use built-in fallback."""
        if self.config_path and os.path.exists(self.config_path):
            self._load_from_yaml(self.config_path)
        else:
            self._load_builtin_fallback()

    def _load_from_yaml(self, config_path: str) -> None:
        """
        Load allowlist from YAML configuration file.

        Args:
            config_path: Path to the YAML configuration file
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not isinstance(config, dict):
                raise ValueError("YAML config must be a dictionary")

            providers = config.get("providers", [])
            if not isinstance(providers, list):
                raise ValueError("'providers' must be a list")

            # Validate provider entries
            for provider in providers:
                if isinstance(provider, dict):
                    provider_id = provider.get("id")
                    if not provider_id or not isinstance(provider_id, str):
                        raise ValueError(f"Invalid provider entry: {provider}")
                    self._providers.add(provider_id)
                elif isinstance(provider, str):
                    self._providers.add(provider)
                else:
                    raise ValueError(f"Invalid provider entry: {provider}")

        except Exception as e:
            print(f"Warning: Failed to load trust registry from {config_path}: {e}")
            print("Falling back to built-in allowlist")
            self._load_builtin_fallback()

    def _load_builtin_fallback(self) -> None:
        """Load built-in fallback allowlist."""
        self._providers = {
            "trusted_bank_001",
            "verified_credit_union_002",
            "authorized_fintech_003",
            "certified_payment_processor_004",
            "licensed_lender_005",
        }

    def is_allowed(self, provider_id: str) -> bool:
        """
        Check if a provider is in the allowlist.

        Args:
            provider_id: Unique identifier for the provider

        Returns:
            bool: True if provider is allowed, False otherwise
        """
        if not isinstance(provider_id, str) or not provider_id.strip():
            return False

        return provider_id.strip() in self._providers

    def list_providers(self) -> list[str]:
        """
        Get list of all allowed providers.

        Returns:
            List of provider IDs in alphabetical order
        """
        return sorted(self._providers)

    def add_provider(self, provider_id: str) -> bool:
        """
        Add a provider to the allowlist.

        Args:
            provider_id: Unique identifier for the provider

        Returns:
            bool: True if added, False if already exists or invalid
        """
        if not isinstance(provider_id, str) or not provider_id.strip():
            return False

        provider_id = provider_id.strip()
        if provider_id in self._providers:
            return False

        self._providers.add(provider_id)
        return True

    def remove_provider(self, provider_id: str) -> bool:
        """
        Remove a provider from the allowlist.

        Args:
            provider_id: Unique identifier for the provider

        Returns:
            bool: True if removed, False if not found
        """
        if not isinstance(provider_id, str):
            return False

        provider_id = provider_id.strip()
        if provider_id not in self._providers:
            return False

        self._providers.remove(provider_id)
        return True

    def reload(self) -> None:
        """Reload the allowlist from the configuration file."""
        self._providers.clear()
        self._load_allowlist()

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about the trust registry.

        Returns:
            Dictionary with registry statistics
        """
        return {
            "total_providers": len(self._providers),
            "allowlist_size": len(self._providers),
        }


# Global instance for the application
def get_trust_registry() -> TrustRegistry:
    """
    Get the global Trust Registry instance.

    Returns:
        TrustRegistry instance
    """
    config_path = os.getenv("TRUST_REGISTRY_CONFIG", "config/trust_registry.yaml")
    return TrustRegistry(config_path)


# Convenience functions for common operations
def is_provider_allowed(provider_id: str) -> bool:
    """
    Check if a provider is allowed (convenience function).

    Args:
        provider_id: Unique identifier for the provider

    Returns:
        bool: True if provider is allowed, False otherwise
    """
    return get_trust_registry().is_allowed(provider_id)


def list_allowed_providers() -> list[str]:
    """
    Get list of all allowed providers (convenience function).

    Returns:
        List of provider IDs
    """
    return get_trust_registry().list_providers()
