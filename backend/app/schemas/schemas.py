"""Pydantic schemas for all API request/response models."""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ── Merchant ──────────────────────────────────────────────

class MerchantBase(BaseModel):
    name: str
    email: str
    description: str = ""
    currency: str = "INR"

class MerchantRead(MerchantBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────────

class ProductBase(BaseModel):
    name: str
    description: str = ""
    category: str
    price: float
    currency: str = "INR"
    stock: int = 0
    active: bool = True
    image_url: str = ""
    tags: List[str] = []
    metadata_extra: dict = {}

class ProductCreate(ProductBase):
    merchant_id: str

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    active: Optional[bool] = None
    image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata_extra: Optional[dict] = None

class ProductRead(ProductBase):
    id: str
    merchant_id: str
    slug: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class CatalogProduct(BaseModel):
    """AI-readable product format."""
    id: str
    name: str
    description: str
    category: str
    price: float
    currency: str
    availability: bool
    stock: int
    tags: List[str]
    purchase_allowed: bool
    class Config:
        from_attributes = True

class CatalogResponse(BaseModel):
    merchant: dict
    products: List[CatalogProduct]


# ── Cart ──────────────────────────────────────────────────

class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1

class CartItemRead(BaseModel):
    id: str
    product_id: str
    product_name: str = ""
    quantity: int
    unit_price: float
    subtotal: float = 0
    class Config:
        from_attributes = True

class CartCreate(BaseModel):
    user_id: str
    merchant_id: str

class CartRead(BaseModel):
    id: str
    user_id: str
    merchant_id: str
    status: str
    items: List[CartItemRead] = []
    subtotal: float = 0
    total: float = 0
    created_at: datetime
    class Config:
        from_attributes = True

class CartCalculation(BaseModel):
    subtotal: float
    discount: float = 0
    tax: float = 0
    total: float
    item_count: int


# ── Order ─────────────────────────────────────────────────

class OrderCreate(BaseModel):
    cart_id: str
    user_id: str
    merchant_id: str
    idempotency_key: Optional[str] = None
    order_type: str = "normal"

class OrderRead(BaseModel):
    id: str
    merchant_id: str
    user_id: str
    cart_id: Optional[str]
    razorpay_order_id: Optional[str]
    amount: float
    currency: str
    status: str
    payment_status: str
    receipt: Optional[str]
    order_type: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ── Payment ───────────────────────────────────────────────

class PaymentCreate(BaseModel):
    order_id: str

class PaymentRead(BaseModel):
    id: str
    order_id: str
    razorpay_payment_id: Optional[str]
    amount: float
    currency: str
    status: str
    method: Optional[str]
    error_code: Optional[str]
    error_description: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ── Policy ────────────────────────────────────────────────

class PolicyRead(BaseModel):
    id: str
    merchant_id: str
    max_purchase_amount: float
    max_discount_percentage: float
    approval_required: bool
    auto_refund_enabled: bool
    allowed_actions: list
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class PolicyUpdate(BaseModel):
    max_purchase_amount: Optional[float] = None
    max_discount_percentage: Optional[float] = None
    approval_required: Optional[bool] = None
    auto_refund_enabled: Optional[bool] = None
    allowed_actions: Optional[list] = None

class PolicyCheckResult(BaseModel):
    allowed: bool
    reason: str
    requires_approval: bool
    details: dict = {}


# ── Audit ─────────────────────────────────────────────────

class AuditLogRead(BaseModel):
    id: str
    actor_type: str
    actor_id: str
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    amount: Optional[float]
    currency: Optional[str]
    reason: Optional[str]
    policy_result: Optional[str]
    approval_status: Optional[str]
    result: Optional[str]
    metadata_extra: dict
    created_at: datetime
    class Config:
        from_attributes = True

class AuditLogCreate(BaseModel):
    actor_type: str
    actor_id: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    reason: Optional[str] = None
    policy_result: Optional[str] = None
    approval_status: Optional[str] = None
    result: Optional[str] = None
    metadata_extra: dict = {}


# ── Agent ─────────────────────────────────────────────────

class AgentActionRead(BaseModel):
    id: str
    session_id: str
    action: str
    tool_name: str
    input_data: dict
    output_data: dict
    status: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: str = "demo_user"
    merchant_id: str = "merchant_001"
    cart_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    products: List[dict] = []
    cart: Optional[dict] = None
    actions: List[dict] = []
    requires_confirmation: bool = False
    confirmation_data: Optional[dict] = None
    agent_steps: List[dict] = []


# ── Analytics ─────────────────────────────────────────────

class RevenueAnalytics(BaseModel):
    total_revenue: float = 0
    total_orders: int = 0
    average_order_value: float = 0
    conversion_rate: float = 0
    ai_assisted_revenue: float = 0
    upsell_revenue: float = 0
    cross_sell_revenue: float = 0
    period: str = "all"

class ProductAnalytics(BaseModel):
    product_id: str
    product_name: str
    total_sold: int
    total_revenue: float
    category: str

class GrowthRecommendation(BaseModel):
    type: str  # cross_sell, upsell, low_conversion, high_demand
    title: str
    description: str
    evidence: str
    recommended_action: str
    estimated_opportunity: float
    products: List[dict] = []


# ── Error ─────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: dict = Field(default_factory=lambda: {
        "code": "UNKNOWN_ERROR",
        "message": "An unknown error occurred.",
        "details": {}
    })
