"""
Tests for Trust Registry v0 functionality.
"""

import os
import tempfile

import yaml

from onyx.trust_registry import (
    TrustRegistry,
    get_trust_registry,
    is_provider_allowed,
    list_allowed_providers,
)


class TestTrustRegistry:
    """Test cases for TrustRegistry class."""

    def test_init_with_builtin_fallback(self):
        """Test initialization with built-in fallback allowlist."""
        registry = TrustRegistry()

        # Should have built-in providers
        assert len(registry.list_providers()) > 0
        assert "trusted_bank_001" in registry.list_providers()

    def test_init_with_nonexistent_config(self):
        """Test initialization with non-existent config file."""
        registry = TrustRegistry("nonexistent_config.yaml")

        # Should fall back to built-in providers
        assert len(registry.list_providers()) > 0
        assert "trusted_bank_001" in registry.list_providers()

    def test_init_with_valid_yaml(self):
        """Test initialization with valid YAML config."""
        # Create temporary YAML file
        yaml_content = {
            "providers": [
                "custom_provider_1",
                "custom_provider_2",
                {"id": "custom_provider_3", "name": "Custom Provider 3"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            registry = TrustRegistry(temp_path)

            providers = registry.list_providers()
            assert "custom_provider_1" in providers
            assert "custom_provider_2" in providers
            assert "custom_provider_3" in providers
            assert len(providers) == 3

        finally:
            os.unlink(temp_path)

    def test_init_with_invalid_yaml(self):
        """Test initialization with invalid YAML config."""
        # Create temporary invalid YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            registry = TrustRegistry(temp_path)

            # Should fall back to built-in providers
            assert len(registry.list_providers()) > 0
            assert "trusted_bank_001" in registry.list_providers()

        finally:
            os.unlink(temp_path)

    def test_is_allowed_true(self):
        """Test is_allowed returns True for allowed providers."""
        registry = TrustRegistry()

        # Test with built-in provider
        assert registry.is_allowed("trusted_bank_001") is True
        assert registry.is_allowed("verified_credit_union_002") is True

    def test_is_allowed_false(self):
        """Test is_allowed returns False for non-allowed providers."""
        registry = TrustRegistry()

        # Test with non-allowed providers
        assert registry.is_allowed("unknown_provider") is False
        assert registry.is_allowed("malicious_provider") is False
        assert registry.is_allowed("") is False

    def test_is_allowed_edge_cases(self):
        """Test is_allowed with edge cases."""
        registry = TrustRegistry()

        # Test with None
        assert registry.is_allowed(None) is False

        # Test with whitespace
        assert registry.is_allowed("  trusted_bank_001  ") is True
        assert registry.is_allowed("   ") is False

    def test_list_providers(self):
        """Test list_providers returns sorted list."""
        registry = TrustRegistry()

        providers = registry.list_providers()

        # Should be a list
        assert isinstance(providers, list)

        # Should be sorted
        assert providers == sorted(providers)

        # Should contain expected providers
        assert "trusted_bank_001" in providers
        assert "verified_credit_union_002" in providers

    def test_add_provider(self):
        """Test adding a provider to the allowlist."""
        registry = TrustRegistry()

        initial_count = len(registry.list_providers())

        # Add new provider
        result = registry.add_provider("new_provider_123")
        assert result is True
        assert "new_provider_123" in registry.list_providers()
        assert len(registry.list_providers()) == initial_count + 1

        # Try to add duplicate
        result = registry.add_provider("new_provider_123")
        assert result is False
        assert len(registry.list_providers()) == initial_count + 1

    def test_add_provider_invalid(self):
        """Test adding invalid providers."""
        registry = TrustRegistry()

        initial_count = len(registry.list_providers())

        # Test with empty string
        result = registry.add_provider("")
        assert result is False
        assert len(registry.list_providers()) == initial_count

        # Test with whitespace only
        result = registry.add_provider("   ")
        assert result is False
        assert len(registry.list_providers()) == initial_count

        # Test with None
        result = registry.add_provider(None)
        assert result is False
        assert len(registry.list_providers()) == initial_count

    def test_remove_provider(self):
        """Test removing a provider from the allowlist."""
        registry = TrustRegistry()

        # Add a provider first
        registry.add_provider("temp_provider_456")
        assert "temp_provider_456" in registry.list_providers()

        # Remove the provider
        result = registry.remove_provider("temp_provider_456")
        assert result is True
        assert "temp_provider_456" not in registry.list_providers()

        # Try to remove non-existent provider
        result = registry.remove_provider("nonexistent_provider")
        assert result is False

    def test_remove_provider_invalid(self):
        """Test removing invalid providers."""
        registry = TrustRegistry()

        initial_count = len(registry.list_providers())

        # Test with None
        result = registry.remove_provider(None)
        assert result is False
        assert len(registry.list_providers()) == initial_count

    def test_reload(self):
        """Test reloading the allowlist."""
        registry = TrustRegistry()

        # Add a provider
        registry.add_provider("temp_provider_789")
        assert "temp_provider_789" in registry.list_providers()

        # Reload (should reset to original state)
        registry.reload()
        assert "temp_provider_789" not in registry.list_providers()
        assert "trusted_bank_001" in registry.list_providers()

    def test_get_stats(self):
        """Test getting registry statistics."""
        registry = TrustRegistry()

        stats = registry.get_stats()

        assert isinstance(stats, dict)
        assert "total_providers" in stats
        assert "allowlist_size" in stats
        assert stats["total_providers"] == stats["allowlist_size"]
        assert stats["total_providers"] > 0


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_is_provider_allowed(self):
        """Test is_provider_allowed convenience function."""
        # Should work with built-in providers
        assert is_provider_allowed("trusted_bank_001") is True
        assert is_provider_allowed("unknown_provider") is False

    def test_list_allowed_providers(self):
        """Test list_allowed_providers convenience function."""
        providers = list_allowed_providers()

        assert isinstance(providers, list)
        assert "trusted_bank_001" in providers

    def test_get_trust_registry(self):
        """Test get_trust_registry function."""
        registry = get_trust_registry()

        assert isinstance(registry, TrustRegistry)
        assert len(registry.list_providers()) > 0
