"""Agent API — chat endpoint and agent management."""

import uuid
from typing import Optional, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.agents.shopping_agent import process_chat
from app.agents.growth_agent import analyze_growth

router = APIRouter()

# In-memory conversation store (use Redis in production)
_conversations: Dict[str, List[Dict]] = {}


@router.post("/agent/chat")
def agent_chat(data: ChatRequest, db: Session = Depends(get_db)):
    """
    Process a chat message through the AI shopping agent.
    Supports multi-turn conversation with tool calling.
    """
    session_id = data.session_id or f"session_{uuid.uuid4().hex[:12]}"

    # Get conversation history
    history = _conversations.get(session_id, [])

    # Process through agent
    result = process_chat(
        db=db,
        message=data.message,
        session_id=session_id,
        user_id=data.user_id,
        merchant_id=data.merchant_id,
        cart_id=data.cart_id,
        conversation_history=history,
    )

    # Store conversation
    history.append({"role": "user", "content": data.message})
    history.append({"role": "assistant", "content": result["message"]})
    _conversations[session_id] = history[-20:]  # Keep last 20 messages

    return result


@router.get("/agent/growth")
def agent_growth(merchant_id: str = "merchant_001", db: Session = Depends(get_db)):
    """Get AI growth analysis for a merchant."""
    return analyze_growth(db, merchant_id)
