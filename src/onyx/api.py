"""
FastAPI application for Onyx Trust Registry service.
"""

from typing import Any

from fastapi import FastAPI

from onyx.mcp.server import mcp_router
from onyx.trust_registry import get_trust_registry

# Create FastAPI application
app = FastAPI(
    title="Onyx Trust Registry",
    description="Trust Registry and KYB (Know Your Business) service for the Open Checkout Network",
    version="0.1.0",
    contact={
        "name": "OCN Team",
        "email": "team@ocn.ai",
        "url": "https://github.com/ahsanazmi1/onyx",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Include MCP router
app.include_router(mcp_router)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        dict: Health status information
    """
    return {"ok": True, "repo": "onyx"}


@app.get("/trust/providers")
async def list_trusted_providers() -> dict[str, Any]:
    """
    List all trusted credential providers.

    Returns:
        dict: List of trusted provider IDs
    """
    registry = get_trust_registry()
    providers = registry.list_providers()
    stats = registry.get_stats()

    return {"providers": providers, "count": len(providers), "stats": stats}


@app.get("/trust/allowed/{provider_id}")
async def check_provider_allowed(provider_id: str) -> dict[str, Any]:
    """
    Check if a specific provider is allowed in the trust registry.

    Args:
        provider_id: Unique identifier for the provider

    Returns:
        dict: Provider status information
    """
    registry = get_trust_registry()
    allowed = registry.is_allowed(provider_id)

    return {
        "provider_id": provider_id,
        "allowed": allowed,
        "reason": (
            "Provider is in trust registry"
            if allowed
            else "Provider not found in trust registry"
        ),
    }


def main() -> None:
    """Main entry point for running the application."""
    import uvicorn

    uvicorn.run(
        "onyx.api:app",
        host="127.0.0.1",  # Use localhost for development security
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
