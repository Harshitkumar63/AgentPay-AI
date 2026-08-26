"""Pydantic schemas for all API request/response models with Pydantic V2 compatibility."""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


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
    model_config = ConfigDict(from_attributes=True)


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
    model_config = ConfigDict(from_attributes=True)

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
    metadata_extra: Optional[dict] = {}
    model_config = ConfigDict(from_attributes=True)

class CatalogResponse(BaseModel):
    merchant: dict
    products: List[CatalogProduct]
    total_products: int = 0


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
    model_config = ConfigDict(from_attributes=True)

class CartCreate(BaseModel):
    user_id: str = "demo_user"
    merchant_id: str = "merchant_001"

class CartRead(BaseModel):
    id: str
    user_id: str
    merchant_id: str
    status: str
    items: List[CartItemRead] = []
    subtotal: float = 0
    total: float = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CartCalculation(BaseModel):
    subtotal: float
    discount: float = 0
    tax: float = 0
    total: float
    item_count: int


# ── Order ─────────────────────────────────────────────────

class OrderCreate(BaseModel):
    cart_id: str
    user_id: str = "demo_user"
    merchant_id: str = "merchant_001"
    idempotency_key: Optional[str] = None
    order_type: str = "normal"

class OrderRead(BaseModel):
    id: str
    merchant_id: str
    user_id: str
    cart_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    payment_status: str
    receipt: Optional[str] = None
    idempotency_key: Optional[str] = None
    order_type: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Payment ───────────────────────────────────────────────

class PaymentCreate(BaseModel):
    order_id: str

class PaymentRead(BaseModel):
    id: str
    order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ── Policy & Risk ─────────────────────────────────────────

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
    model_config = ConfigDict(from_attributes=True)

class PolicyUpdate(BaseModel):
    max_purchase_amount: Optional[float] = None
    max_discount_percentage: Optional[float] = None
    approval_required: Optional[bool] = None
    auto_refund_enabled: Optional[bool] = None
    allowed_actions: Optional[list] = None

class PolicyCheckResult(BaseModel):
    allowed: bool
    policy_id: Optional[str] = None
    risk_level: str = "LOW"
    risk_score: int = 10
    requires_approval: bool = False
    reason: str
    details: dict = {}

class PolicySimulateRequest(BaseModel):
    merchant_id: str = "merchant_001"
    amount: float
    discount_percentage: float = 0.0
    action: str = "create_order"

class PolicySimulateResponse(BaseModel):
    simulation: bool = True
    input: dict
    decision: PolicyCheckResult


# ── Audit ─────────────────────────────────────────────────

class AuditLogRead(BaseModel):
    id: str
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
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

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


# ── Webhook Events ────────────────────────────────────────

class WebhookEventRead(BaseModel):
    id: str
    event_id: Optional[str] = None
    event_type: str
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    status: str
    payload: dict = {}
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Agent & AI Buyer API ──────────────────────────────────

class AgentActionRead(BaseModel):
    id: str
    session_id: str
    action: str
    tool_name: str
    input_data: dict
    output_data: dict
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

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
    cart_id: Optional[str] = None
    actions: List[dict] = []
    requires_confirmation: bool = False
    confirmation_data: Optional[dict] = None
    agent_steps: List[dict] = []
    explanation: Optional[dict] = None
    demo_mode: bool = False

# AI Buyer API Schemas (Phase 5)
class BuyerSearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    color: Optional[str] = None
    merchant_id: str = "merchant_001"
    limit: int = 10

class BuyerCheckoutRequest(BaseModel):
    cart_id: str
    user_id: str = "ai_buyer_agent"
    merchant_id: str = "merchant_001"
    idempotency_key: Optional[str] = None
    order_type: str = "ai_assisted"


# ── Merchant AI Copilot & Campaigns (Phase 26 & 27) ───────

class CopilotQueryRequest(BaseModel):
    query: str
    merchant_id: str = "merchant_001"

class CopilotQueryResponse(BaseModel):
    answer: str
    metrics_used: dict = {}
    suggested_actions: List[str] = []
    proposed_campaign: Optional[dict] = None

class CampaignProposal(BaseModel):
    id: str
    title: str
    target_segment: str
    product_id: str
    product_name: str
    discount_percentage: float
    budget: float
    duration_days: int
    estimated_opportunity: float
    risk_level: str = "HIGH"
    status: str = "proposed"  # proposed, approved, rejected, active


# ── Analytics ─────────────────────────────────────────────

class RevenueAnalytics(BaseModel):
    total_revenue: float = 0
    total_orders: int = 0
    successful_orders: int = 0
    average_order_value: float = 0
    conversion_rate: float = 0
    ai_assisted_revenue: float = 0
    upsell_revenue: float = 0
    cross_sell_revenue: float = 0
    failed_payments_count: int = 0
    blocked_actions_count: int = 0
    period: str = "last_30_days"

class ProductAnalytics(BaseModel):
    product_id: str
    product_name: str
    total_sold: int
    total_revenue: float
    category: str
    stock: int = 0

class GrowthRecommendation(BaseModel):
    type: str  # cross_sell, upsell, low_conversion, high_demand, high_stock
    title: str
    description: str
    evidence: str
    recommended_action: str
    estimated_opportunity: float
    products: List[dict] = []


# ── Error ─────────────────────────────────────────────────

class ErrorDetails(BaseModel):
    code: str
    message: str
    details: dict = {}

class ErrorResponse(BaseModel):
    error: ErrorDetails


# ── Budget, Trust & Approvals ─────────────────────────────

class AgentBudgetRead(BaseModel):
    id: str
    agent_id: str
    merchant_id: str
    daily_limit: float
    per_transaction_limit: float
    spent_today: float
    remaining_daily_budget: float
    model_config = ConfigDict(from_attributes=True)

class AgentBudgetUpdate(BaseModel):
    daily_limit: Optional[float] = None
    per_transaction_limit: Optional[float] = None

class AgentTrustRead(BaseModel):
    id: str
    agent_id: str
    trust_score: int
    successful_transactions: int
    failed_payments: int
    policy_violations: int
    duplicate_requests: int
    approval_rate: float
    risk_tier: str
    model_config = ConfigDict(from_attributes=True)

class ApprovalCreate(BaseModel):
    agent_session_id: Optional[str] = None
    order_id: Optional[str] = None
    merchant_id: str = "merchant_001"
    user_id: str = "demo_user"
    action: str = "create_order"
    amount: float
    currency: str = "INR"
    reason: str = "High-risk financial action requires human authorization"

class ApprovalRead(BaseModel):
    id: str
    agent_session_id: Optional[str] = None
    order_id: Optional[str] = None
    merchant_id: str
    user_id: str
    action: str
    amount: float
    currency: str
    risk_level: str
    risk_score: int
    policy_result: dict
    reason: str
    status: str  # PENDING, APPROVED, REJECTED, EXPIRED
    decision_reason: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    decided_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class ApprovalDecisionRequest(BaseModel):
    status: str  # APPROVED or REJECTED
    approved_by: str = "merchant_admin"
    reason: Optional[str] = None

class DecisionReplayResponse(BaseModel):
    order_id: str
    session_id: Optional[str] = None
    user_request: Optional[str] = None
    stages: List[dict] = []
    policy_check: Optional[dict] = None
    risk_assessment: Optional[dict] = None
    budget_check: Optional[dict] = None
    trust_check: Optional[dict] = None
    approval_record: Optional[dict] = None
    payment_status: Optional[dict] = None
    audit_logs: List[dict] = []

class MCPCallRequest(BaseModel):
    tool_name: str
    arguments: dict = {}
    session_id: Optional[str] = None
    user_id: str = "mcp_agent"
    merchant_id: str = "merchant_001"

class MCPCallResponse(BaseModel):
    tool_name: str
    result: Any
    duration_ms: int
    status: str

