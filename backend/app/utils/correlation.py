"""Request Correlation Context and Utilities for Distributed Tracing."""

import uuid
from contextvars import ContextVar
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context Variables for async task-local request correlation
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
session_id_ctx: ContextVar[str] = ContextVar("session_id", default="")
agent_id_ctx: ContextVar[str] = ContextVar("agent_id", default="")


def get_current_request_id() -> str:
    """Retrieve current request ID or generate a fallback."""
    req_id = request_id_ctx.get()
    return req_id or f"req_{uuid.uuid4().hex[:10]}"


def get_current_session_id() -> str:
    """Retrieve current session ID or generate a fallback."""
    sess_id = session_id_ctx.get()
    return sess_id or f"sess_{uuid.uuid4().hex[:10]}"


def get_current_agent_id() -> str:
    """Retrieve current authenticated agent ID."""
    return agent_id_ctx.get() or "default_agent"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to extract or inject X-Request-ID, X-Session-ID, and X-Agent-ID."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:10]}"
        sess_id = request.headers.get("X-Session-ID") or f"sess_{uuid.uuid4().hex[:10]}"
        agent_id = request.headers.get("X-Agent-ID") or "anonymous"

        token_req = request_id_ctx.set(req_id)
        token_sess = session_id_ctx.set(sess_id)
        token_agent = agent_id_ctx.set(agent_id)

        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Session-ID"] = sess_id
            return response
        finally:
            request_id_ctx.reset(token_req)
            session_id_ctx.reset(token_sess)
            agent_id_ctx.reset(token_agent)
