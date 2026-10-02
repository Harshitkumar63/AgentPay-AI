"""Model Context Protocol (MCP) Compatible Integration Layer (Phase 20)."""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import (
    product_service,
    cart_service,
    recommendation_service,
    order_service,
    policy_service,
    audit_service,
    payment_service,
    budget_service,
    trust_service,
    approval_service,
    agent_registry_service,
)
from app.utils.correlation import get_current_request_id, get_current_session_id

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])

MCP_TOOLS_SPEC = [
    {
        "name": "search_products",
        "description": "Search catalog products by keywords, category, price range, or color with stock verification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keywords"},
                "category": {"type": "string", "description": "Category (shoes, electronics, fitness, bags)"},
                "max_price": {"type": "number", "description": "Maximum budget ceiling"},
                "min_price": {"type": "number", "description": "Minimum price"},
                "color": {"type": "string", "description": "Color preference"},
            },
        },
        "required_permission": "product.search",
    },
    {
        "name": "get_product",
        "description": "Fetch verified factual product details, specifications, and live inventory count.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID (e.g. prod_001)"},
            },
            "required": ["product_id"],
        },
        "required_permission": "catalog.read",
    },
    {
        "name": "compare_products",
        "description": "Compare 2+ products side-by-side on price, features, pros, cons, and suitability.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_ids": {"type": "array", "items": {"type": "string"}, "description": "List of product IDs to compare"},
            },
            "required": ["product_ids"],
        },
        "required_permission": "product.compare",
    },
    {
        "name": "create_cart",
        "description": "Initialize a dedicated shopping cart session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User identifier"},
                "merchant_id": {"type": "string", "description": "Merchant ID"},
            },
        },
        "required_permission": "cart.create",
    },
    {
        "name": "add_to_cart",
        "description": "Add an item to the shopping cart with authoritative database pricing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cart_id": {"type": "string", "description": "Cart ID"},
                "product_id": {"type": "string", "description": "Product ID"},
                "quantity": {"type": "integer", "description": "Quantity to add (default 1)"},
            },
            "required": ["cart_id", "product_id"],
        },
        "required_permission": "cart.write",
    },
    {
        "name": "get_cart",
        "description": "Fetch current cart items and server-calculated totals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cart_id": {"type": "string", "description": "Cart ID"},
            },
            "required": ["cart_id"],
        },
        "required_permission": "cart.write",
    },
    {
        "name": "get_recommendations",
        "description": "Get cross-sell, upsell, and complementary product recommendations with affinity scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Source product ID"},
                "recommendation_type": {"type": "string", "enum": ["cross_sell", "upsell", "similar"]},
            },
            "required": ["product_id"],
        },
        "required_permission": "recommendation.read",
    },
    {
        "name": "evaluate_policy",
        "description": "Simulate and verify if a transaction complies with merchant purchase caps and discount limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Transaction amount in INR"},
                "discount_percentage": {"type": "number", "description": "Discount percentage requested"},
            },
            "required": ["amount"],
        },
        "required_permission": "catalog.read",
    },
    {
        "name": "evaluate_risk",
        "description": "Calculate continuous 0-100 deterministic risk score and approval requirements.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "Proposed action name"},
                "amount": {"type": "number", "description": "Transaction amount"},
            },
            "required": ["action"],
        },
        "required_permission": "catalog.read",
    },
    {
        "name": "get_agent_budget",
        "description": "Retrieve agent spending limits, daily budget, and remaining balance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent identifier"},
            },
        },
        "required_permission": "analytics.read",
    },
    {
        "name": "get_agent_trust",
        "description": "Retrieve server-calculated agent trust score, factor breakdown, and dynamic spending tiers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent identifier"},
            },
        },
        "required_permission": "analytics.read",
    },
    {
        "name": "request_approval",
        "description": "Request human-in-the-loop authorization with 5-minute expiring TTL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Transaction amount"},
                "reason": {"type": "string", "description": "Justification for transaction"},
                "order_id": {"type": "string", "description": "Optional associated order ID"},
            },
            "required": ["amount"],
        },
        "required_permission": "approval.request",
    },
    {
        "name": "create_order",
        "description": "Formulate a governed order through the 12-state order machine with stock and policy gating.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cart_id": {"type": "string", "description": "Cart ID"},
                "user_id": {"type": "string", "description": "Customer ID"},
                "merchant_id": {"type": "string", "description": "Merchant ID"},
                "idempotency_key": {"type": "string", "description": "Unique idempotency key"},
            },
            "required": ["cart_id"],
        },
        "required_permission": "order.create",
    },
    {
        "name": "get_order_status",
        "description": "Query order status, payment status, and timeline steps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
            },
            "required": ["order_id"],
        },
        "required_permission": "order.read",
    },
    {
        "name": "get_payment_status",
        "description": "Retrieve verified payment status from database records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
            },
            "required": ["order_id"],
        },
        "required_permission": "payment.read",
    },
    {
        "name": "get_audit_trace",
        "description": "Retrieve cryptographic audit log records for an order or session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
            },
            "required": ["order_id"],
        },
        "required_permission": "audit.read",
    },
]


class MCPCallPayload(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    agent_id: Optional[str] = "ShoppingBot"
    session_id: Optional[str] = None
    user_id: Optional[str] = "mcp_user"
    merchant_id: Optional[str] = "merchant_001"


@router.get("/tools", summary="List All 16 MCP-Compatible Commerce Tools")
def get_mcp_tools():
    """Returns tool schemas compatible with Model Context Protocol specification."""
    return {
        "mcp_version": "1.0",
        "protocol": "Model Context Protocol",
        "service": "AgentPay AI Governed Commerce Engine",
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["inputSchema"],
                "required_permission": t.get("required_permission"),
            }
            for t in MCP_TOOLS_SPEC
        ],
    }


@router.post("/call", summary="Execute MCP Commerce Tool under Strict Governance")
def call_mcp_tool(
    req: MCPCallPayload,
    x_agent_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Executes an MCP tool with full security pipeline:
    1. Authenticate Agent / Key
    2. Enforce Scoped Permissions
    3. Execute Deterministic Tool Logic
    4. Enforce Budget & Policies
    5. Log Tamper-Evident Audit Event
    """
    start = time.time()
    req_id = get_current_request_id()
    sess_id = req.session_id or get_current_session_id()
    agent_id = req.agent_id or "ShoppingBot"

    # 1. Authenticate if API key provided
    if x_agent_key:
        auth_agent = agent_registry_service.authenticate_api_key(db, x_agent_key)
        if auth_agent:
            agent_id = auth_agent.id

    # Find required permission for tool
    tool_spec = next((t for t in MCP_TOOLS_SPEC if t["name"] == req.tool_name), None)
    required_perm = tool_spec["required_permission"] if tool_spec else "catalog.read"

    # 2. Check Permissions
    perm_check = agent_registry_service.check_agent_permission(db, agent_id, required_perm, request_id=req_id)
    if not perm_check["allowed"]:
        return {
            "tool_name": req.tool_name,
            "status": "BLOCKED",
            "error_code": perm_check.get("error_code", "PERMISSION_DENIED"),
            "result": {"error": True, "message": perm_check.get("message", "Permission denied")},
            "duration_ms": int((time.time() - start) * 1000),
        }

    # 3. Tool Execution
    args = req.arguments
    result: Any = None
    status = "SUCCESS"

    try:
        if req.tool_name == "search_products":
            prods = product_service.search_products(
                db,
                query=args.get("query"),
                category=args.get("category"),
                max_price=args.get("max_price"),
                min_price=args.get("min_price"),
                color=args.get("color"),
                merchant_id=req.merchant_id,
            )
            result = {
                "count": len(prods),
                "products": [
                    {"id": p.id, "name": p.name, "category": p.category, "price": p.price, "in_stock": p.stock > 0}
                    for p in prods
                ],
            }

        elif req.tool_name == "get_product":
            p = product_service.get_product(db, args.get("product_id", ""))
            result = {"product": {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock} if p else None}

        elif req.tool_name == "compare_products":
            result = product_service.compare_products(db, args.get("product_ids", []))

        elif req.tool_name == "create_cart":
            cart = cart_service.get_or_create_cart(db, user_id=req.user_id, merchant_id=req.merchant_id)
            result = cart_service.get_cart_details(db, cart.id)

        elif req.tool_name == "add_to_cart":
            cart_id = args.get("cart_id")
            if not cart_id:
                cart = cart_service.get_or_create_cart(db, user_id=req.user_id, merchant_id=req.merchant_id)
                cart_id = cart.id
            cart_item = cart_service.add_item(db, cart_id, args.get("product_id"), quantity=args.get("quantity", 1))
            result = cart_service.get_cart_details(db, cart_id)

        elif req.tool_name == "get_cart":
            result = cart_service.get_cart_details(db, args.get("cart_id"))

        elif req.tool_name == "get_recommendations":
            result = {
                "recommendations": recommendation_service.get_recommendations(
                    db,
                    product_id=args.get("product_id"),
                    recommendation_type=args.get("recommendation_type", "cross_sell"),
                )
            }

        elif req.tool_name == "evaluate_policy":
            result = policy_service.simulate_policy(
                db,
                merchant_id=req.merchant_id,
                amount=args.get("amount", 0.0),
                discount_percentage=args.get("discount_percentage", 0.0),
                agent_id=agent_id,
            )

        elif req.tool_name == "evaluate_risk":
            result = policy_service.calculate_dynamic_risk_score(
                action=args.get("action", "create_order"),
                amount=args.get("amount", 0.0),
            )

        elif req.tool_name == "get_agent_budget":
            target_ag = args.get("agent_id") or agent_id
            b = budget_service.get_or_create_budget(db, agent_id=target_ag, merchant_id=req.merchant_id)
            result = {
                "agent_id": b.agent_id,
                "daily_limit": b.daily_limit,
                "spent_today": b.spent_today,
                "remaining_daily_budget": b.remaining_daily_budget,
                "per_transaction_limit": b.per_transaction_limit,
            }

        elif req.tool_name == "get_agent_trust":
            result = trust_service.get_trust_assessment(db, agent_id=args.get("agent_id") or agent_id)

        elif req.tool_name == "request_approval":
            appr = approval_service.create_approval_request(
                db=db,
                amount=args.get("amount", 0.0),
                action="mcp_request",
                reason=args.get("reason", "Requested via MCP tool"),
                order_id=args.get("order_id"),
                merchant_id=req.merchant_id,
            )
            result = {"approval_id": appr.id, "status": appr.status, "expires_at": str(appr.expires_at)}

        elif req.tool_name == "create_order":
            result = order_service.create_order(
                db=db,
                cart_id=args.get("cart_id"),
                user_id=args.get("user_id", req.user_id),
                merchant_id=req.merchant_id,
                idempotency_key=args.get("idempotency_key"),
                actor_id=agent_id,
                actor_type="ai_agent",
            )

        elif req.tool_name in ("get_order_status", "get_order"):
            order = order_service.get_order(db, args.get("order_id"))
            result = order_service._order_to_dict(order) if order else {"error": "Order not found"}

        elif req.tool_name == "get_payment_status":
            result = payment_service.get_payment_status(db, args.get("order_id"))

        elif req.tool_name == "get_audit_trace":
            logs = audit_service.get_audit_logs(db, limit=20)
            result = {"logs": [{"id": l.id, "action": l.action, "result": l.result, "hash": l.event_hash} for l in logs]}

        else:
            result = {"error": True, "message": f"Unknown tool '{req.tool_name}'"}
            status = "FAILED"

    except Exception as e:
        status = "FAILED"
        result = {"error": True, "message": str(e)}

    duration_ms = int((time.time() - start) * 1000)

    # 4. Audit Log
    audit_service.create_audit_log(
        db=db,
        actor_type="ai_agent",
        actor_id=agent_id,
        action=f"MCP_TOOL_{req.tool_name.upper()}",
        resource_type="mcp",
        resource_id=req.tool_name,
        result=status,
        agent_id=agent_id,
        request_id=req_id,
        session_id=sess_id,
        metadata_extra={"arguments": args, "duration_ms": duration_ms},
    )

    return {
        "tool_name": req.tool_name,
        "result": result,
        "duration_ms": duration_ms,
        "status": status,
    }
