"""
MCP (Model Context Protocol) server for Onyx Trust Registry.

Provides standardized interface for trust registry operations.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Create MCP router
mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPRequest(BaseModel):
    """MCP request model."""

    verb: str
    args: dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP response model."""

    success: bool
    data: dict[str, Any]
    error: str | None = None


@mcp_router.post("/invoke")
async def invoke_mcp(request: MCPRequest) -> MCPResponse:
    """
    MCP invoke endpoint.

    Handles Model Context Protocol requests for Onyx Trust Registry operations.

    Args:
        request: MCP request with verb and arguments

    Returns:
        MCP response with success status and data

    Raises:
        HTTPException: For invalid verbs or missing required parameters
    """
    try:
        if request.verb == "getStatus":
            return MCPResponse(success=True, data={"ok": True, "agent": "onyx"})

        elif request.verb == "isAllowedProvider":
            provider_id = request.args.get("provider_id")
            if not provider_id:
                raise HTTPException(
                    status_code=400, detail="provider_id parameter is required"
                )

            # Stub implementation - deterministic based on provider_id
            # In real implementation, this would query the trust registry
            allowed = _is_provider_allowed(provider_id)
            reason = (
                "Provider is in trust registry"
                if allowed
                else "Provider not found in trust registry"
            )

            return MCPResponse(
                success=True,
                data={"allowed": allowed, "provider_id": provider_id, "reason": reason},
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unknown verb: {request.verb}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        ) from e


def _is_provider_allowed(provider_id: str) -> bool:
    """
    Determine if a provider is allowed in the trust registry.

    This is a stub implementation that returns deterministic results
    based on the provider_id for testing purposes.

    Args:
        provider_id: Unique identifier for the provider

    Returns:
        bool: True if provider is allowed, False otherwise
    """
    # Stub logic: allow providers with IDs starting with "trusted_"
    # or containing "verified", deny others
    provider_lower = provider_id.lower()

    if provider_lower.startswith("trusted_"):
        return True
    elif "verified" in provider_lower:
        return True
    elif provider_lower.startswith("blocked_"):
        return False
    elif "suspicious" in provider_lower:
        return False
    else:
        # Default: allow if provider_id length is even, deny if odd
        # This provides deterministic behavior for testing
        return len(provider_id) % 2 == 0
