"""
LLM Provider Abstraction — supports OpenAI, Gemini, and demo mode.

Uses structured tool/function calling for agent behavior.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger("agentpay.llm")


class LLMProvider:
    """Abstract LLM provider with tool calling support."""

    def __init__(self):
        self.provider = settings.ai_provider
        self._client = None

        if settings.ai_configured:
            if self.provider == "openai":
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=settings.openai_api_key)
                    logger.info("OpenAI client initialized")
                except Exception as e:
                    logger.warning(f"Failed to init OpenAI: {e}")
            elif self.provider == "gemini":
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.google_api_key)
                    self._client = genai
                    logger.info("Gemini client initialized")
                except Exception as e:
                    logger.warning(f"Failed to init Gemini: {e}")

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send chat with tool definitions.
        Returns: {"content": str, "tool_calls": [...] or None}
        """
        if not self.is_configured:
            return self._demo_response(messages, tools)

        if self.provider == "openai":
            return self._openai_chat(messages, tools, model or settings.openai_model)
        elif self.provider == "gemini":
            return self._gemini_chat(messages, tools, model or settings.gemini_model)

        return self._demo_response(messages, tools)

    def _openai_chat(self, messages: List[Dict], tools: List[Dict], model: str) -> Dict:
        """OpenAI chat with function calling."""
        try:
            openai_tools = [
                {
                    "type": "function",
                    "function": tool,
                }
                for tool in tools
            ]

            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto",
            )

            choice = response.choices[0]
            result = {"content": choice.message.content or ""}

            if choice.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments),
                    }
                    for tc in choice.message.tool_calls
                ]
            else:
                result["tool_calls"] = None

            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"content": f"I'm having trouble connecting to my AI service. Error: {str(e)}", "tool_calls": None}

    def _gemini_chat(self, messages: List[Dict], tools: List[Dict], model: str) -> Dict:
        """Gemini chat with function calling."""
        try:
            import google.generativeai as genai
            from google.generativeai.types import content_types

            # Convert tools to Gemini format
            gemini_tools = []
            for tool in tools:
                func_decl = genai.protos.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters=genai.protos.Schema(
                        type=genai.protos.Type.OBJECT,
                        properties={
                            k: genai.protos.Schema(type=genai.protos.Type.STRING)
                            for k in tool.get("parameters", {}).get("properties", {})
                        },
                    ),
                )
                gemini_tools.append(func_decl)

            gm = genai.GenerativeModel(model)
            # Convert messages
            gemini_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append({"role": role, "parts": [msg["content"]]})

            response = gm.generate_content(
                gemini_messages,
                tools=[genai.protos.Tool(function_declarations=gemini_tools)] if gemini_tools else None,
            )

            result = {"content": "", "tool_calls": None}

            for part in response.parts:
                if part.text:
                    result["content"] += part.text
                if part.function_call:
                    if result["tool_calls"] is None:
                        result["tool_calls"] = []
                    result["tool_calls"].append({
                        "id": f"call_{part.function_call.name}",
                        "name": part.function_call.name,
                        "arguments": dict(part.function_call.args),
                    })

            return result

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {"content": f"I'm having trouble with my AI service. Error: {str(e)}", "tool_calls": None}

    def _demo_response(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """
        Demo mode: parse user intent and generate tool calls without a real LLM.
        This provides a functional experience without AI API keys.
        """
        last_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_message = msg["content"].lower()
                break

        # Simple intent matching for demo mode
        tool_names = [t["name"] for t in tools]

        # Search intent
        if any(word in last_message for word in ["find", "search", "show", "looking", "need", "want", "recommend"]):
            # Extract price constraints
            args = {"query": last_message}
            if "under" in last_message or "below" in last_message:
                import re
                price_match = re.search(r'(?:under|below)\s*₹?\s*(\d+)', last_message)
                if price_match:
                    args["max_price"] = float(price_match.group(1))

            # Extract category
            categories = ["shoes", "electronics", "bags", "fitness", "clothing", "accessories", "laptop", "phone", "backpack"]
            for cat in categories:
                if cat in last_message:
                    args["category"] = cat
                    break

            # Extract color
            colors = ["black", "blue", "red", "white", "grey", "navy"]
            for color in colors:
                if color in last_message:
                    args["color"] = color
                    break

            if "search_products" in tool_names:
                return {
                    "content": "",
                    "tool_calls": [{"id": "call_search", "name": "search_products", "arguments": args}],
                }

        # Buy/purchase intent
        if any(word in last_message for word in ["buy", "purchase", "order", "checkout"]):
            if "create_order" in tool_names:
                return {
                    "content": "I'll help you complete the purchase. Let me check your cart and create an order.",
                    "tool_calls": [{"id": "call_cart", "name": "get_cart", "arguments": {}}],
                }

        # Cart intent
        if any(word in last_message for word in ["cart", "add", "remove"]):
            if "add" in last_message and "add_to_cart" in tool_names:
                return {
                    "content": "",
                    "tool_calls": [{"id": "call_add", "name": "get_cart", "arguments": {}}],
                }
            if "get_cart" in tool_names:
                return {
                    "content": "",
                    "tool_calls": [{"id": "call_cart", "name": "get_cart", "arguments": {}}],
                }

        # Compare intent
        if "compare" in last_message:
            if "search_products" in tool_names:
                return {
                    "content": "",
                    "tool_calls": [{"id": "call_search", "name": "search_products", "arguments": {"query": last_message}}],
                }

        # Default: just respond
        return {
            "content": "I'm running in demo mode (no AI API key configured). I can still help you search products, manage your cart, and process orders. Try asking me to 'find running shoes under ₹3000' or 'show me laptops'!",
            "tool_calls": None,
        }


# Singleton
llm_provider = LLMProvider()
