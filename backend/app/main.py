"""
AgentPay AI — FastAPI Application Entry Point

Main application with CORS, routers, and startup events.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentpay")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown events."""
    logger.info("🚀 Starting AgentPay AI...")
    init_db()
    logger.info(f"📦 Database initialized ({'SQLite' if settings.is_sqlite else 'PostgreSQL'})")
    logger.info(f"🤖 AI Provider: {settings.ai_provider} ({'configured' if settings.ai_configured else 'DEMO MODE'})")
    logger.info(f"💳 Razorpay: {'configured' if settings.razorpay_configured else 'DEMO MODE'}")
    logger.info(f"🎯 Demo Mode: {settings.demo_mode}")

    # Auto-seed in demo mode
    if settings.demo_mode:
        from app.db.seed import seed_database
        seed_database()
        logger.info("🌱 Demo data seeded")

    yield
    logger.info("👋 AgentPay AI shutting down...")


app = FastAPI(
    title="AgentPay AI",
    description="Agentic Commerce, FinTech, and AI Governance Platform",
    version="2.5.0",
    lifespan=lifespan,
)

from app.utils.correlation import CorrelationMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CorrelationMiddleware)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Headers"] = "*"
        headers["Access-Control-Allow-Methods"] = "*"

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(exc) if settings.debug else "An internal error occurred.",
                "details": {}
            }
        },
        headers=headers,
    )


# Health check
@app.get("/health")
@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "service": "AgentPay AI",
        "demo_mode": settings.demo_mode,
        "ai_configured": settings.ai_configured,
        "razorpay_configured": settings.razorpay_configured,
    }


@app.get("/health/ready")
@app.get("/api/health/ready")
async def health_ready():
    return {
        "status": "ready",
        "database": "connected",
        "governance_engine": "active",
        "circuit_breaker": "active",
    }


@app.get("/health/live")
@app.get("/api/health/live")
async def health_live():
    return {
        "status": "alive",
        "service": "AgentPay AI",
    }


# Import and register routers
from app.api import (
    products,
    cart,
    orders,
    payments,
    analytics,
    agent,
    policies,
    audit,
    webhooks,
    buyer_api,
    approvals,
    budget_trust,
    campaigns,
    mcp_api,
    agents_registry,
    admin_agents,
    admin_system,
    admin_approvals,
    agent_manifest,
    notifications,
    negotiation,
    pricing,
    inventory,
    refunds,
    support,
    customer_memory,
    cart_optimizer,
    simulator,
    experiments,
    live_stream,
    a2a_commerce,
)

app.include_router(agent_manifest.router)
app.include_router(admin_agents.router, prefix="/api", tags=["Admin Agent Registry"])
app.include_router(admin_system.router, prefix="/api", tags=["Admin System Controls"])
app.include_router(admin_approvals.router, prefix="/api", tags=["Admin Human Approvals"])
app.include_router(notifications.router, prefix="/api", tags=["Notification Center"])

app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(cart.router, prefix="/api", tags=["Cart"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(payments.router, prefix="/api", tags=["Payments"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics"])
app.include_router(agent.router, prefix="/api", tags=["Agent"])
app.include_router(policies.router, prefix="/api", tags=["Policies"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(buyer_api.router, prefix="/api", tags=["AI Buyer API (v1)"])
app.include_router(approvals.router, prefix="/api", tags=["Human Approvals"])
app.include_router(budget_trust.router, prefix="/api", tags=["Agent Budget & Trust"])
app.include_router(campaigns.router, prefix="/api", tags=["AI Campaign Builder"])
app.include_router(mcp_api.router, prefix="/api", tags=["Model Context Protocol (MCP)"])

# Newly registered advanced routers
app.include_router(agents_registry.router, prefix="/api", tags=["Multi-Agent Registry & Governance"])
app.include_router(negotiation.router, prefix="/api", tags=["AI Negotiation Engine"])
app.include_router(pricing.router, prefix="/api", tags=["Dynamic Pricing Simulator"])
app.include_router(inventory.router, prefix="/api", tags=["AI Inventory Agent"])
app.include_router(refunds.router, prefix="/api", tags=["Refund Workflow"])
app.include_router(support.router, prefix="/api", tags=["Customer Support Agent"])
app.include_router(customer_memory.router, prefix="/api", tags=["Customer Memory & Preferences"])
app.include_router(cart_optimizer.router, prefix="/api", tags=["Cart Optimizer"])
app.include_router(simulator.router, prefix="/api", tags=["What-If Business Simulator"])
app.include_router(experiments.router, prefix="/api", tags=["AI A/B Testing"])
app.include_router(live_stream.router, prefix="/api", tags=["Real-time Agent Event Stream"])
app.include_router(a2a_commerce.router, prefix="/api", tags=["Agent-to-Agent Commerce"])

