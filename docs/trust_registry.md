# Trust Registry v0

The Trust Registry v0 provides allowlist functionality for credential providers in the Open Checkout Network (OCN) ecosystem. It maintains a list of trusted providers that are authorized to participate in OCN operations.

## Overview

The Trust Registry serves as a central authority for determining which credential providers are trusted and allowed to operate within the OCN ecosystem. It provides:

- **Allowlist Management**: Maintain a list of trusted credential providers
- **Provider Verification**: Check if a specific provider is authorized
- **Configuration Management**: Load provider lists from YAML configuration files
- **API Endpoints**: RESTful API for trust verification operations

## Configuration

### YAML Configuration File

The Trust Registry can be configured using a YAML file. Copy the sample configuration:

```bash
cp config/trust_registry.sample.yaml config/trust_registry.yaml
```

### Configuration Structure

```yaml
# Trust Registry Configuration
providers:
  # Simple string format
  - "provider_id_1"
  - "provider_id_2"

  # Object format with metadata
  - id: "provider_id_3"
    name: "Provider Name"
    type: "bank"
    status: "active"
    verified: true

# Configuration metadata
metadata:
  version: "v0"
  created_at: "2024-09-22"
  description: "Trust Registry v0 allowlist for OCN credential providers"
  maintainer: "OCN Team"

# Registry settings
settings:
  strict_mode: true      # Only allow providers in allowlist
  auto_reload: false     # Auto-reload config on changes
  cache_ttl: 300         # Cache TTL in seconds
```

### Environment Variables

- `TRUST_REGISTRY_CONFIG`: Path to the trust registry configuration file (default: `config/trust_registry.yaml`)

## API Endpoints

### List Trusted Providers

**GET** `/trust/providers`

Returns a list of all trusted credential providers.

**Response:**
```json
{
  "providers": [
    "authorized_fintech_003",
    "certified_payment_processor_004",
    "licensed_lender_005",
    "trusted_bank_001",
    "verified_credit_union_002"
  ],
  "count": 5,
  "stats": {
    "total_providers": 5,
    "allowlist_size": 5
  }
}
```

### Check Provider Status

**GET** `/trust/allowed/{provider_id}`

Check if a specific provider is allowed in the trust registry.

**Parameters:**
- `provider_id` (path): Unique identifier for the provider

**Response (Allowed Provider):**
```json
{
  "provider_id": "trusted_bank_001",
  "allowed": true,
  "reason": "Provider is in trust registry"
}
```

**Response (Non-allowed Provider):**
```json
{
  "provider_id": "unknown_provider",
  "allowed": false,
  "reason": "Provider not found in trust registry"
}
```

## Python API

### Basic Usage

```python
from onyx.trust_registry import get_trust_registry, is_provider_allowed, list_allowed_providers

# Get registry instance
registry = get_trust_registry()

# Check if provider is allowed
is_allowed = registry.is_allowed("trusted_bank_001")
print(f"Provider allowed: {is_allowed}")

# List all providers
providers = registry.list_providers()
print(f"Trusted providers: {providers}")

# Get statistics
stats = registry.get_stats()
print(f"Registry stats: {stats}")
```

### Convenience Functions

```python
# Quick check
if is_provider_allowed("provider_id"):
    print("Provider is trusted")

# Get all providers
all_providers = list_allowed_providers()
print(f"Total providers: {len(all_providers)}")
```

### Advanced Usage

```python
from onyx.trust_registry import TrustRegistry

# Create registry with custom config
registry = TrustRegistry("path/to/custom/config.yaml")

# Add provider dynamically
registry.add_provider("new_provider_123")

# Remove provider
registry.remove_provider("old_provider_456")

# Reload configuration
registry.reload()
```

## Built-in Providers

The Trust Registry includes a built-in allowlist that serves as a fallback when no configuration file is available:

- `trusted_bank_001` - First National Bank
- `verified_credit_union_002` - Community Credit Union
- `authorized_fintech_003` - TechPay Solutions
- `certified_payment_processor_004` - SecurePay Inc
- `licensed_lender_005` - QuickLoan Services

## Error Handling

The Trust Registry handles various error conditions gracefully:

- **Missing Config File**: Falls back to built-in allowlist
- **Invalid YAML**: Falls back to built-in allowlist with warning
- **Invalid Provider IDs**: Returns `False` for `is_allowed()` checks
- **Empty Config**: Falls back to built-in allowlist

## Security Considerations

- **Strict Mode**: When enabled, only providers in the allowlist are permitted
- **Case Sensitivity**: Provider IDs are case-sensitive
- **Whitespace Handling**: Leading/trailing whitespace is trimmed
- **Validation**: All provider IDs are validated before processing

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI
from onyx.trust_registry import get_trust_registry

app = FastAPI()
registry = get_trust_registry()

@app.get("/verify/{provider_id}")
async def verify_provider(provider_id: str):
    allowed = registry.is_allowed(provider_id)
    return {"provider_id": provider_id, "allowed": allowed}
```

### Middleware Integration

```python
from fastapi import FastAPI, HTTPException
from onyx.trust_registry import is_provider_allowed

async def trust_middleware(request):
    provider_id = request.headers.get("X-Provider-ID")
    if provider_id and not is_provider_allowed(provider_id):
        raise HTTPException(status_code=403, detail="Provider not trusted")
```

## Monitoring and Logging

The Trust Registry provides statistics and logging capabilities:

```python
# Get registry statistics
stats = registry.get_stats()
print(f"Total providers: {stats['total_providers']}")
print(f"Allowlist size: {stats['allowlist_size']}")
```

## Best Practices

1. **Configuration Management**: Use version control for trust registry configurations
2. **Regular Updates**: Periodically review and update the allowlist
3. **Monitoring**: Monitor API usage and provider verification requests
4. **Backup**: Maintain backups of configuration files
5. **Documentation**: Keep provider metadata up to date

## Troubleshooting

### Common Issues

1. **Provider Not Found**: Check provider ID spelling and case sensitivity
2. **Config Not Loading**: Verify YAML syntax and file permissions
3. **Empty Allowlist**: Check configuration file format and content

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

registry = TrustRegistry("config/trust_registry.yaml")
```

## Future Enhancements

- **Provider Metadata**: Extended provider information and verification status
- **Dynamic Updates**: Real-time allowlist updates without service restart
- **Audit Logging**: Comprehensive logging of trust verification requests
- **Rate Limiting**: Protection against abuse of trust verification endpoints
- **Caching**: Improved performance with configurable caching strategies
