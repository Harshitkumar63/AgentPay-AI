"""Agent Manifest API — Machine-readable capabilities at /.well-known/agent.json (Phase 21)."""

from fastapi import APIRouter

router = APIRouter(tags=["Agent Manifest"])


@router.get("/.well-known/agent.json", summary="Machine-Readable Agent Capabilities Manifest")
@router.get("/api/.well-known/agent.json", summary="Machine-Readable Agent Capabilities Manifest (API Prefix)")
def get_agent_manifest():
    """
    Exposes machine-readable capabilities, governance invariants, and authentication protocols
    for autonomous buyer agents and MCP orchestrators without revealing secrets.
    """
    return {
        "name": "AgentPay AI",
        "version": "2.5.0",
        "description": "Governed infrastructure and deterministic payment gateway for autonomous AI commerce",
        "homepage": "https://github.com/Harshitkumar63/AgentPay-AI",
        "capabilities": [
            "catalog.search",
            "product.compare",
            "recommendation.read",
            "cart.create",
            "cart.write",
            "checkout.request",
            "order.status",
            "payment.status",
            "a2a.negotiation",
            "mcp.tools",
        ],
        "authentication": {
            "type": "api_key",
            "header": "X-Agent-Key",
            "bearer_supported": True,
            "key_format": "agp_<token>",
        },
        "governance": {
            "principle": "AI proposes. Deterministic backend decides.",
            "policy_enforced": True,
            "continuous_risk_scoring": True,
            "human_approval_ttl_minutes": 5,
            "circuit_breaker_enabled": True,
            "velocity_limiter_enabled": True,
            "tamper_evident_audit_trail": True,
        },
        "protocols": {
            "mcp_tools_url": "/api/mcp/tools",
            "mcp_call_url": "/api/mcp/call",
            "a2a_discovery_url": "/api/a2a/discovery",
            "a2a_offer_url": "/api/a2a/offer",
            "a2a_accept_url": "/api/a2a/accept",
            "ai_buyer_catalog_url": "/api/agent/v1/catalog",
        },
    }
