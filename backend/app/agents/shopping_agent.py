"""Shopping Agent — Multi-tool calling agent with real-time reasoning and execution trace."""

import uuid
import time
import json
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.llm_provider import llm_provider
from app.agents.prompts import SHOPPING_AGENT_SYSTEM_PROMPT
from app.services import (
    product_service,
    cart_service,
    recommendation_service,
    order_service,
    policy_service,
    audit_service,
    payment_service,
    analytics_service,
)

logger = logging.getLogger("agentpay.agent")

MAX_TOOL_CALLS = 8

# In-memory customer session context memory (Phase 32)
_customer_contexts: Dict[str, Dict[str, Any]] = {}

TOOL_DEFINITIONS = [
    {
        "name": "search_products",
        "description": "Search products in the catalog using natural language filters (query, category, price range, color). Returns verified products.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords"},
                "category": {"type": "string", "description": "Category (e.g., shoes, electronics, bags, fitness, clothing, accessories)"},
                "max_price": {"type": "number", "description": "Maximum price in INR"},
                "min_price": {"type": "number", "description": "Minimum price in INR"},
                "color": {"type": "string", "description": "Color filter"},
            },
        },
    },
    {
        "name": "get_product",
        "description": "Get detailed factual information about a specific product by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID (e.g., prod_001)"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Verify live inventory availability for a product before purchasing.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID"},
                "quantity": {"type": "integer", "description": "Quantity requested"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "recommend_products",
        "description": "Get algorithmic product recommendations (cross_sell, upsell, similar).",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Target product ID"},
                "recommendation_type": {"type": "string", "enum": ["cross_sell", "upsell", "similar"], "description": "Recommendation algorithm"},
            },
            "required": ["product_id", "recommendation_type"],
        },
    },
    {
        "name": "compare_products",
        "description": "Compare two or more products side-by-side on price, features, pros, cons, and suitability.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to compare",
                },
            },
            "required": ["product_ids"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add an item with verified price to the customer's cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to add"},
                "quantity": {"type": "integer", "description": "Quantity (default 1)"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "remove_from_cart",
        "description": "Remove an item from the current cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to remove"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_cart",
        "description": "Fetch current cart items, subtotal, and calculated totals.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "calculate_cart",
        "description": "Calculate exact cart pricing on the server.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "create_order",
        "description": "Initiate order creation with inventory validation, policy gating, and risk evaluation.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_type": {"type": "string", "enum": ["normal", "ai_assisted", "upsell", "cross_sell"]},
            },
        },
    },
    {
        "name": "get_order",
        "description": "Retrieve order information by Order ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_payment_status",
        "description": "Fetch verified payment status for an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "merchant_revenue_analytics",
        "description": "Get merchant revenue metrics and performance statistics.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_customer_context",
        "description": "Retrieve the current customer shopping session memory (preferences, budget, search history).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_policy",
        "description": "Check current merchant purchase and discount policies.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "request_purchase_approval",
        "description": "Trigger the human approval gate for high-risk financial actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Purchase amount"},
                "reason": {"type": "string", "description": "Reason for purchase approval"},
            },
            "required": ["amount"],
        },
    },
]


def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    db: Session,
    session_id: str,
    user_id: str,
    merchant_id: str,
    cart_id: Optional[str],
) -> tuple[Any, Optional[str]]:
    """Execute an agent tool through backend service layers."""
    start_time = time.time()
    result = None
    new_cart_id = cart_id

    try:
        if tool_name == "search_products":
            products = product_service.search_products(
                db,
                query=arguments.get("query"),
                category=arguments.get("category"),
                max_price=arguments.get("max_price"),
                min_price=arguments.get("min_price"),
                color=arguments.get("color"),
                tags=arguments.get("tags"),
                merchant_id=merchant_id,
            )
            result = {
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "description": p.description,
                        "category": p.category,
                        "price": p.price,
                        "currency": p.currency,
                        "stock": p.stock,
                        "tags": p.tags or [],
                        "image_url": p.image_url,
                        "available": p.stock > 0 and p.active,
                    }
                    for p in products
                ],
                "count": len(products),
            }

        elif tool_name == "get_product":
            product = product_service.get_product(db, arguments["product_id"])
            if product:
                result = {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "category": product.category,
                    "price": product.price,
                    "currency": product.currency,
                    "stock": product.stock,
                    "tags": product.tags or [],
                    "image_url": product.image_url,
                    "available": product.stock > 0 and product.active,
                    "metadata": product.metadata_extra or {},
                }
            else:
                result = {"error": "Product not found"}

        elif tool_name == "check_inventory":
            result = product_service.check_inventory(
                db, arguments["product_id"], arguments.get("quantity", 1)
            )

        elif tool_name == "recommend_products":
            result = recommendation_service.get_recommendations(
                db,
                product_id=arguments["product_id"],
                recommendation_type=arguments["recommendation_type"],
                merchant_id=merchant_id,
            )

        elif tool_name == "compare_products":
            result = product_service.compare_products(db, arguments.get("product_ids", []))

        elif tool_name == "add_to_cart":
            if not cart_id:
                cart = cart_service.get_or_create_cart(db, user_id, merchant_id)
                new_cart_id = cart.id
            else:
                new_cart_id = cart_id

            item = cart_service.add_item(
                db, new_cart_id, arguments["product_id"], arguments.get("quantity", 1)
            )
            if item:
                result = cart_service.get_cart_details(db, new_cart_id)
            else:
                result = {"error": "Could not add item to cart (insufficient stock or invalid product)"}

        elif tool_name == "remove_from_cart":
            if cart_id:
                success = cart_service.remove_item(db, cart_id, arguments["product_id"])
                if success:
                    result = cart_service.get_cart_details(db, cart_id)
                else:
                    result = {"error": "Item not found in cart"}
            else:
                result = {"error": "No active cart"}

        elif tool_name == "get_cart":
            if cart_id:
                result = cart_service.get_cart_details(db, cart_id)
            else:
                result = {"items": [], "subtotal": 0, "total": 0, "item_count": 0, "message": "Cart is empty"}

        elif tool_name == "calculate_cart":
            if cart_id:
                result = cart_service.calculate_cart(db, cart_id)
            else:
                result = {"subtotal": 0, "discount": 0, "tax": 0, "total": 0, "item_count": 0}

        elif tool_name == "create_order":
            if not cart_id:
                result = {"error": "No active cart. Please add items before placing order."}
            else:
                order_result = order_service.create_order(
                    db,
                    cart_id=cart_id,
                    user_id=user_id,
                    merchant_id=merchant_id,
                    order_type=arguments.get("order_type", "ai_assisted"),
                    actor_id=f"agent_{session_id}",
                    actor_type="ai_agent",
                )
                result = order_result

        elif tool_name == "get_order":
            order = order_service.get_order(db, arguments["order_id"])
            if order:
                result = order_service._order_to_dict(order)
            else:
                result = {"error": "Order not found"}

        elif tool_name == "get_payment_status":
            result = payment_service.get_payment_status(db, arguments["order_id"])

        elif tool_name == "merchant_revenue_analytics":
            result = analytics_service.get_revenue_analytics(db, merchant_id)

        elif tool_name == "get_customer_context":
            result = _customer_contexts.get(session_id, {"session_id": session_id, "preferences": {}})

        elif tool_name == "get_policy":
            policy = policy_service.get_merchant_policy(db, merchant_id)
            if policy:
                result = {
                    "max_purchase_amount": policy.max_purchase_amount,
                    "max_discount_percentage": policy.max_discount_percentage,
                    "approval_required": policy.approval_required,
                    "allowed_actions": policy.allowed_actions,
                }
            else:
                result = {"message": "Standard default policy active"}

        elif tool_name == "request_purchase_approval":
            amount = arguments.get("amount", 0.0)
            policy_res = policy_service.check_purchase_policy(db, merchant_id, amount)
            result = {
                "requires_approval": True,
                "amount": amount,
                "policy": policy_res,
                "reason": arguments.get("reason", "Sensitive financial transaction confirmation required"),
            }

        else:
            result = {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}", exc_info=True)
        result = {"error": f"Tool execution failed: {str(e)}"}

    duration_ms = int((time.time() - start_time) * 1000)
    audit_service.create_agent_action(
        db,
        session_id=session_id,
        action=f"execute_{tool_name}",
        tool_name=tool_name,
        input_data=arguments,
        output_data=result if isinstance(result, dict) else {"data": str(result)[:500]},
        status="success" if not (isinstance(result, dict) and "error" in result) else "error",
        duration_ms=duration_ms,
    )

    return result, new_cart_id


def process_chat(
    db: Session,
    message: str,
    session_id: Optional[str] = None,
    user_id: str = "demo_user",
    merchant_id: str = "merchant_001",
    cart_id: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """Process a chat message through the agent loop."""
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:12]}"

    # Update session memory (Phase 32)
    ctx = _customer_contexts.get(session_id, {"session_id": session_id, "user_id": user_id})
    _update_session_context(ctx, message)
    _customer_contexts[session_id] = ctx

    messages = [{"role": "system", "content": SHOPPING_AGENT_SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history[-10:])
    messages.append({"role": "user", "content": message})

    agent_steps = []
    products_found = []
    cart_data = None
    requires_confirmation = False
    confirmation_data = None
    current_cart_id = cart_id
    tool_call_count = 0
    explanation = None

    is_demo = not llm_provider.is_configured

    while tool_call_count < MAX_TOOL_CALLS:
        response = llm_provider.chat_with_tools(messages, TOOL_DEFINITIONS)

        if not response.get("tool_calls"):
            break

        for tool_call in response["tool_calls"]:
            tool_call_count += 1
            if tool_call_count > MAX_TOOL_CALLS:
                break

            tool_name = tool_call["name"]
            arguments = tool_call.get("arguments", {})

            # If search in demo mode and context has remembered preferences, enrich query
            if tool_name == "search_products" and ctx.get("preferences"):
                if not arguments.get("max_price") and ctx["preferences"].get("budget"):
                    arguments["max_price"] = ctx["preferences"]["budget"]
                if not arguments.get("category") and ctx["preferences"].get("category"):
                    arguments["category"] = ctx["preferences"]["category"]
                if not arguments.get("color") and ctx["preferences"].get("color"):
                    arguments["color"] = ctx["preferences"]["color"]

            logger.info(f"Agent tool call [{tool_call_count}/{MAX_TOOL_CALLS}]: {tool_name}")

            tool_result, current_cart_id = execute_tool(
                tool_name, arguments, db, session_id, user_id, merchant_id, current_cart_id
            )

            agent_steps.append({
                "step": tool_call_count,
                "tool": tool_name,
                "input": arguments,
                "output_summary": _summarize_output(tool_result),
                "status": "error" if isinstance(tool_result, dict) and "error" in tool_result else "success",
            })

            if tool_name == "search_products" and isinstance(tool_result, dict):
                found = tool_result.get("products", [])
                products_found.extend(found)
                if found:
                    top_prod = found[0]
                    explanation = policy_service.explain_decision(
                        "search_products",
                        {
                            "product_name": top_prod.get("name"),
                            "category_match": arguments.get("category"),
                            "color_match": arguments.get("color"),
                            "budget": arguments.get("max_price"),
                            "in_stock": top_prod.get("stock", 0) > 0,
                            "is_top_rated": True,
                        },
                    )

            if tool_name in ("add_to_cart", "get_cart", "remove_from_cart") and isinstance(tool_result, dict):
                cart_data = tool_result

            if tool_name == "create_order" and isinstance(tool_result, dict):
                if tool_result.get("requires_approval") or tool_result.get("status") == "created":
                    requires_confirmation = True
                    order_info = tool_result.get("order", {})
                    confirmation_data = {
                        "type": "purchase_confirmation",
                        "order": order_info,
                        "policy": tool_result.get("policy", {}),
                        "amount": order_info.get("amount", 0),
                        "message": tool_result.get("message", ""),
                    }
                    explanation = policy_service.explain_decision("create_order", {})

            tool_result_str = json.dumps(tool_result, default=str)[:2000]
            messages.append({"role": "assistant", "content": f"[Tool: {tool_name}] Called with: {json.dumps(arguments)}"})
            messages.append({"role": "user", "content": f"[Tool Result: {tool_name}] {tool_result_str}"})

        if is_demo:
            break

    final_message = response.get("content", "")

    if is_demo and not final_message:
        final_message = _generate_demo_response(products_found, cart_data, agent_steps, requires_confirmation)

    if not final_message and products_found:
        final_message = f"I found {len(products_found)} product(s) matching your request."

    if not final_message:
        final_message = "I processed your request. How can I help you further?"

    return {
        "message": final_message,
        "session_id": session_id,
        "products": products_found[:10],
        "cart": cart_data,
        "cart_id": current_cart_id,
        "actions": [{"type": s["tool"], "status": s["status"]} for s in agent_steps],
        "requires_confirmation": requires_confirmation,
        "confirmation_data": confirmation_data,
        "agent_steps": agent_steps,
        "explanation": explanation,
        "demo_mode": is_demo,
    }


def _update_session_context(ctx: dict, message: str):
    """Remember preferences across user interaction turns (Phase 32)."""
    import re
    msg = message.lower()
    prefs = ctx.setdefault("preferences", {})

    # Budget
    price_match = re.search(r'(?:under|below|budget|less than)\s*₹?\s*(\d+)', msg)
    if price_match:
        prefs["budget"] = float(price_match.group(1))

    # Category
    categories = ["shoes", "running shoes", "electronics", "bags", "fitness", "clothing", "accessories", "laptop", "phone"]
    for cat in categories:
        if cat in msg:
            prefs["category"] = cat
            break

    # Color
    colors = ["black", "blue", "white", "red", "grey", "navy", "green"]
    for col in colors:
        if col in msg:
            prefs["color"] = col
            break


def _generate_demo_response(products: list, cart: dict | None, steps: list, requires_confirm: bool) -> str:
    """Generate dynamic formatted text response for demo mode."""
    parts = []
    if products:
        parts.append(f"I found **{len(products)} verified product(s)** in the store catalog:\n")
        for p in products[:4]:
            stock_badge = f"✅ In Stock ({p.get('stock')} available)" if p.get('available', True) else "❌ Out of stock"
            parts.append(f"• **{p['name']}** — **₹{p['price']:,.2f}** ({stock_badge})")
            if p.get('description'):
                desc = p['description'][:90] + ("..." if len(p['description']) > 90 else "")
                parts.append(f"  _{desc}_")

        parts.append("\n💡 *Tip: Click 'Add to Cart' or 'Buy Now' to proceed with policy-gated checkout.*")
    elif cart and cart.get("items"):
        items = cart["items"]
        parts.append(f"Your shopping cart currently has **{len(items)} item(s)**:\n")
        for item in items:
            parts.append(f"• **{item.get('product_name', 'Product')}** × {item.get('quantity', 1)} — ₹{item.get('subtotal', 0):,.2f}")
        parts.append(f"\n💰 **Subtotal: ₹{cart.get('subtotal', 0):,.2f} | Total: ₹{cart.get('total', 0):,.2f}**")
        parts.append("\nReady to complete your purchase? Say **'Buy now'** or click **'Confirm Checkout'**.")
    elif requires_confirm:
        parts.append("🛡️ **Order Prepared & Gated by Policy Engine!**\nPlease review the purchase summary below and confirm authorization.")
    elif steps:
        for s in steps:
            icon = "❌" if s["status"] == "error" else "⚡"
            parts.append(f"{icon} **{s['tool']}**: {s['output_summary']}")
    else:
        parts.append("I am your AgentPay AI shopping assistant. How can I help you today?")

    return "\n".join(parts)


def _summarize_output(result: Any) -> str:
    """Create concise summary of tool output for UI trace."""
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        if "products" in result:
            return f"Retrieved {result.get('count', len(result['products']))} items"
        if "items" in result:
            return f"Cart has {len(result.get('items', []))} item(s) (₹{result.get('total', 0):,.0f})"
        if "order" in result:
            return f"Created order {result['order'].get('id', '')} (₹{result['order'].get('amount', 0):,.0f})"
        if "available" in result:
            return f"{'Stock confirmed' if result['available'] else 'Out of stock'}"
        if "recommendation" in result:
            return f"Comparison pick: {result['recommendation'].get('recommended_product_name')}"
        return str(result)[:120]
    if isinstance(result, list):
        return f"{len(result)} items"
    return str(result)[:120]
