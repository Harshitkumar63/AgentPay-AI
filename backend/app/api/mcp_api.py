"""Model Context Protocol (MCP) Compatible Integration Layer (Phase 36)."""

import time
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.agents.shopping_agent import TOOL_DEFINITIONS, execute_tool
from app.schemas.schemas import MCPCallRequest, MCPCallResponse

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (MCP)"])


@router.get("/tools", summary="List MCP-Compatible Commerce Tools")
def get_mcp_tools():
    """Returns tool schemas compatible with Model Context Protocol and standard LLM tool calling."""
    return {
        "mcp_version": "1.0",
        "protocol": "Model Context Protocol",
        "service": "AgentPay AI Commerce Engine",
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "inputSchema": t["parameters"],
            }
            for t in TOOL_DEFINITIONS
        ],
    }


@router.post("/call", response_model=MCPCallResponse, summary="Execute MCP Commerce Tool")
def call_mcp_tool(
    req: MCPCallRequest,
    db: Session = Depends(get_db),
):
    """Execute any commerce tool directly through the MCP interface."""
    start = time.time()
    session_id = req.session_id or "mcp_session"

    result, _, status = execute_tool(
        tool_name=req.tool_name,
        arguments=req.arguments,
        db=db,
        session_id=session_id,
        user_id=req.user_id,
        merchant_id=req.merchant_id,
        cart_id=None,
    )
    duration_ms = int((time.time() - start) * 1000)

    return MCPCallResponse(
        tool_name=req.tool_name,
        result=result,
        duration_ms=duration_ms,
        status=status,
    )
