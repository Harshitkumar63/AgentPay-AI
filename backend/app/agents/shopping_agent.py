"""
Shopping Agent — Tool-calling agent with multi-step reasoning.

Implements the agent loop:
USER REQUEST → LLM → Tool Selection → Tool Execution → LLM → Response
"""

import uuid
import time
import json
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.agents.llm_provider import llm_provider
from app.agents.prompts import SHOPPING_AGENT_SYSTEM_PROMPT
from app.services import product_service, cart_service, recommendation_service, order_service, policy_service, audit_service, payment_service

logger = logging.getLogger("agentpay.agent")

MAX_TOOL_CALLS = 8

# Tool definitions for the LLM
TOOL_DEFINITIONS = [
    {
        "name": "search_products",
        "description": "Search products in the store catalog. Use this to find products matching user queries. Returns matching products with details.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text (e.g., 'running shoes', 'laptop')"},
                "category": {"type": "string", "description": "Product category filter (e.g., 'shoes', 'electronics', 'bags', 'fitness', 'clothing', 'accessories')"},
                "max_price": {"type": "number", "description": "Maximum price in INR"},
                "min_price": {"type": "number", "description": "Minimum price in INR"},
                "color": {"type": "string", "description": "Color filter (e.g., 'black', 'blue')"},
            },
        },
    },
    {
        "name": "get_product",
        "description": "Get detailed information about a specific product by its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID (e.g., 'prod_001')"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "check_inventory",
        "description": "Check if a product is available in the required quantity.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to check"},
                "quantity": {"type": "integer", "description": "Quantity needed (default: 1)"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "recommend_products",
        "description": "Get product recommendations. Types: 'cross_sell' (complementary products), 'upsell' (premium alternatives), 'similar' (same category).",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to get recommendations for"},
                "recommendation_type": {"type": "string", "enum": ["cross_sell", "upsell", "similar"], "description": "Type of recommendation"},
            },
            "required": ["product_id", "recommendation_type"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add a product to the shopping cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to add"},
                "quantity": {"type": "integer", "description": "Quantity to add (default: 1)"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "remove_from_cart",
        "description": "Remove a product from the shopping cart.",
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
        "description": "View current shopping cart contents and totals.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "calculate_cart",
        "description": "Calculate cart totals including subtotal, discount, tax, and total.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "create_order",
        "description": "Create an order from the current cart. This will validate inventory, check policy limits, and require user approval. Only call this when the user explicitly wants to buy.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_type": {"type": "string", "enum": ["normal", "ai_assisted", "upsell", "cross_sell"], "description": "Type of order for analytics"},
            },
        },
    },
    {
        "name": "get_payment_status",
        "description": "Check the payment status of an order.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to check"},
            },
            "required": ["order_id"],
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
    """
    Execute an agent tool and return (result, updated_cart_id).
    All tool execution goes through proper service layers.
    """
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
                        "id": p.id, "name": p.name, "description": p.description,
                        "category": p.category, "price": p.price, "currency": p.currency,
                        "stock": p.stock, "tags": p.tags or [], "image_url": p.image_url,
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
                    "id": product.id, "name": product.name, "description": product.description,
                    "category": product.category, "price": product.price, "currency": product.currency,
                    "stock": product.stock, "tags": product.tags or [], "image_url": product.image_url,
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

        elif tool_name == "add_to_cart":
            # Get or create cart
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
                result = {"error": "Could not add item to cart"}

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
                result = {"error": "No active cart. Please add items first."}
            else:
                # This goes through: validation → inventory → policy → approval → order
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

        elif tool_name == "get_payment_status":
            result = payment_service.get_payment_status(db, arguments["order_id"])

        else:
            result = {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}", exc_info=True)
        result = {"error": f"Tool execution failed: {str(e)}"}

    # Record agent action
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
    """
    Process a chat message through the agent loop.

    Flow:
    1. Build messages with system prompt + history + user message
    2. Call LLM with tool definitions
    3. If LLM wants to call tools → execute them → feed results back
    4. Repeat until LLM returns a text response or max calls reached
    5. Return structured response
    """
    if not session_id:
        session_id = f"session_{uuid.uuid4().hex[:12]}"

    # Build messages
    messages = [{"role": "system", "content": SHOPPING_AGENT_SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history[-10:])  # Keep last 10 messages

    messages.append({"role": "user", "content": message})

    agent_steps = []
    products_found = []
    cart_data = None
    requires_confirmation = False
    confirmation_data = None
    current_cart_id = cart_id
    tool_call_count = 0

    is_demo = not llm_provider.is_configured

    while tool_call_count < MAX_TOOL_CALLS:
        # Call LLM
        response = llm_provider.chat_with_tools(messages, TOOL_DEFINITIONS)

        if not response.get("tool_calls"):
            # LLM gave a text response — we're done
            break

        # Execute tools
        for tool_call in response["tool_calls"]:
            tool_call_count += 1
            if tool_call_count > MAX_TOOL_CALLS:
                break

            tool_name = tool_call["name"]
            arguments = tool_call.get("arguments", {})

            logger.info(f"Agent tool call [{tool_call_count}/{MAX_TOOL_CALLS}]: {tool_name}({json.dumps(arguments)[:200]})")

            # Execute tool
            tool_result, current_cart_id = execute_tool(
                tool_name, arguments, db, session_id, user_id, merchant_id, current_cart_id
            )

            # Track step
            agent_steps.append({
                "step": tool_call_count,
                "tool": tool_name,
                "input": arguments,
                "output_summary": _summarize_output(tool_result),
                "status": "error" if isinstance(tool_result, dict) and "error" in tool_result else "success",
            })

            # Track products found
            if tool_name == "search_products" and isinstance(tool_result, dict):
                products_found.extend(tool_result.get("products", []))

            # Track cart
            if tool_name in ("add_to_cart", "get_cart", "remove_from_cart") and isinstance(tool_result, dict):
                cart_data = tool_result

            # Track order creation (requires confirmation)
            if tool_name == "create_order" and isinstance(tool_result, dict):
                if tool_result.get("requires_approval"):
                    requires_confirmation = True
                    confirmation_data = {
                        "type": "purchase_confirmation",
                        "order": tool_result.get("order", {}),
                        "policy": tool_result.get("policy", {}),
                        "amount": tool_result.get("order", {}).get("amount", 0),
                        "message": tool_result.get("message", ""),
                    }

            # Add tool result to messages for next LLM call
            tool_result_str = json.dumps(tool_result, default=str)[:2000]
            messages.append({"role": "assistant", "content": f"[Tool: {tool_name}] Called with: {json.dumps(arguments)}"})
            messages.append({"role": "user", "content": f"[Tool Result: {tool_name}] {tool_result_str}"})

        # In demo mode, only do ONE round of tool calls, then generate response
        if is_demo:
            break

    # Build final response
    final_message = response.get("content", "")

    # In demo mode, generate a rich text response from tool results
    if is_demo and not final_message:
        final_message = _generate_demo_response(products_found, cart_data, agent_steps, requires_confirmation)

    if tool_call_count >= MAX_TOOL_CALLS and not final_message:
        final_message = "I've completed several steps to help you. Here's what I found."

    if not final_message and products_found:
        final_message = f"I found {len(products_found)} product(s) matching your request."

    if not final_message:
        final_message = "I processed your request. How can I help you further?"

    return {
        "message": final_message,
        "session_id": session_id,
        "products": products_found[:10],  # Limit products in response
        "cart": cart_data,
        "cart_id": current_cart_id,
        "actions": [{"type": s["tool"], "status": s["status"]} for s in agent_steps],
        "requires_confirmation": requires_confirmation,
        "confirmation_data": confirmation_data,
        "agent_steps": agent_steps,
        "demo_mode": is_demo,
    }


def _generate_demo_response(products: list, cart: dict | None, steps: list, requires_confirm: bool) -> str:
    """Generate a rich text response in demo mode from tool results."""
    parts = []

    if products:
        parts.append(f"I found **{len(products)} product(s)** matching your search! Here they are:")
        for p in products[:5]:
            stock_text = f"✅ {p.get('stock', 0)} in stock" if p.get('available', True) else "❌ Out of stock"
            parts.append(f"• **{p['name']}** — ₹{p['price']:,.0f} ({stock_text})")
        if len(products) > 5:
            parts.append(f"...and {len(products) - 5} more.")
        parts.append("\nWould you like to add any of these to your cart, or want me to recommend alternatives?")
    elif cart and cart.get("items"):
        items = cart["items"]
        parts.append(f"Your cart has **{len(items)} item(s)**:")
        for item in items:
            parts.append(f"• {item.get('product_name', 'Product')} × {item.get('quantity', 1)} — ₹{item.get('subtotal', 0):,.0f}")
        parts.append(f"\n**Total: ₹{cart.get('total', 0):,.0f}**")
        parts.append("\nReady to checkout? Just say \"buy these items\"!")
    elif requires_confirm:
        parts.append("Your order is ready for confirmation! Please review and approve.")
    elif steps:
        for s in steps:
            if s["status"] == "error":
                parts.append(f"⚠️ {s['output_summary']}")
            else:
                parts.append(f"✅ {s['tool']}: {s['output_summary']}")
    else:
        parts.append("I'm here to help! Try asking me to 'find running shoes' or 'show me laptops'.")

    return "\n".join(parts)


def _summarize_output(result: Any) -> str:
    """Create a brief summary of tool output for display."""
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        if "products" in result:
            return f"Found {result.get('count', len(result['products']))} products"
        if "items" in result:
            return f"Cart with {len(result.get('items', []))} items"
        if "order" in result:
            return f"Order {result['order'].get('id', 'created')}"
        if "available" in result:
            return f"{'Available' if result['available'] else 'Not available'}"
        return str(result)[:100]
    if isinstance(result, list):
        return f"{len(result)} results"
    return str(result)[:100]
