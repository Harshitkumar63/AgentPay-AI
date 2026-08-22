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
    description="AI-Powered Agentic Commerce for Modern Merchants",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred.",
                "details": {}
            }
        }
    )


# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "AgentPay AI",
        "demo_mode": settings.demo_mode,
        "ai_configured": settings.ai_configured,
        "razorpay_configured": settings.razorpay_configured,
    }


# Import and register routers
from app.api import products, cart, orders, payments, analytics, agent, policies, audit, webhooks, buyer_api

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

