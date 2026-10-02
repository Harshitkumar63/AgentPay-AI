"""Pydantic schemas for all API request/response models with Pydantic V2 compatibility."""

from datetime import datetime, date
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
    discount: float = 0
    tax: float = 0
    total: float = 0
    item_count: int = 0
    model_config = ConfigDict(from_attributes=True)


# ── Order ─────────────────────────────────────────────────

class OrderCreate(BaseModel):
    cart_id: str
    user_id: str = "demo_user"
    merchant_id: str = "merchant_001"
    idempotency_key: Optional[str] = None
    order_type: str = "normal"  # normal, ai_assisted, upsell, cross_sell

class OrderRead(BaseModel):
    id: str
    merchant_id: str
    user_id: str
    cart_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_session_id: Optional[str] = None
    approval_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: str
    payment_status: str
    receipt: Optional[str] = None
    order_type: str = "normal"
    timeline: List[dict] = []
    decision_factors: dict = {}
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Payment ───────────────────────────────────────────────

class PaymentCreate(BaseModel):
    order_id: str

class PaymentVerify(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class PaymentRead(BaseModel):
    id: str
    order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    status: str
    method: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── Policy & Risk ─────────────────────────────────────────

class PolicyBase(BaseModel):
    max_purchase_amount: float = 50000.0
    max_discount_percentage: float = 20.0
    approval_required: bool = True
    auto_refund_enabled: bool = False
    allowed_actions: List[str] = ["search", "recommend", "add_to_cart", "create_order"]

class PolicyUpdate(BaseModel):
    max_purchase_amount: Optional[float] = None
    max_discount_percentage: Optional[float] = None
    approval_required: Optional[bool] = None
    auto_refund_enabled: Optional[bool] = None
    allowed_actions: Optional[List[str]] = None

class PolicyRead(PolicyBase):
    id: str
    merchant_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PolicyCheckResult(BaseModel):
    allowed: bool
    policy_id: Optional[str] = None
    risk_level: str
    risk_score: int
    requires_approval: bool
    reason: str
    details: dict = {}

class PolicySimulateRequest(BaseModel):
    merchant_id: str = "merchant_001"
    amount: float
    discount_percentage: float = 0.0
    action: str = "create_order"
    agent_id: str = "default_agent"

class PolicySimulateResponse(BaseModel):
    simulation: bool = True
    input: dict
    decision: dict


# ── Audit & Trace ─────────────────────────────────────────

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

class AgentActionRead(BaseModel):
    id: str
    session_id: str
    request_id: Optional[str] = None
    tool_call_id: Optional[str] = None
    sequence_number: int = 1
    action: str
    tool_name: str
    event_type: str = "TOOL_EXECUTION"
    input_data: dict = {}
    output_data: dict = {}
    status: str
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ── AI Agents & Multi-Agent Registry ──────────────────────

class AgentBase(BaseModel):
    name: str
    description: str = ""
    role: str = "shopping"
    status: str = "ACTIVE"  # ACTIVE, PAUSED, DISABLED, SUSPENDED
    permissions: List[str] = ["CATALOG_READ", "PRODUCT_READ", "CART_WRITE", "ORDER_CREATE"]
    daily_budget: float = 10000.0
    per_transaction_limit: float = 5000.0
    hourly_limit: float = 7500.0

class AgentCreate(AgentBase):
    id: Optional[str] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[List[str]] = None
    daily_budget: Optional[float] = None
    per_transaction_limit: Optional[float] = None
    hourly_limit: Optional[float] = None

class AgentRead(AgentBase):
    id: str
    trust_score: int = 90
    risk_level: str = "LOW"
    circuit_breaker_tripped: bool = False
    circuit_breaker_reason: Optional[str] = None
    failed_payment_count: int = 0
    is_active: bool = True
    created_at: datetime
    last_activity: datetime
    model_config = ConfigDict(from_attributes=True)

class AgentKillSwitchRequest(BaseModel):
    status: str = "PAUSED"  # ACTIVE, PAUSED, DISABLED
    reason: Optional[str] = "Manual merchant kill switch activation"


# ── Agent Budget & Trust ──────────────────────────────────

class AgentBudgetRead(BaseModel):
    id: str
    agent_id: str
    merchant_id: str
    daily_limit: float
    per_transaction_limit: float
    hourly_limit: float = 7500.0
    spent_today: float
    spent_this_hour: float = 0.0
    remaining_daily_budget: float
    remaining_hourly_budget: float = 7500.0
    model_config = ConfigDict(from_attributes=True)

class AgentBudgetUpdate(BaseModel):
    daily_limit: Optional[float] = None
    per_transaction_limit: Optional[float] = None
    hourly_limit: Optional[float] = None

class AgentTrustRead(BaseModel):
    id: str
    agent_id: str
    trust_score: int
    successful_transactions: int
    failed_payments: int
    policy_violations: int
    duplicate_requests: int
    velocity_violations: int = 0
    approval_rate: float
    risk_tier: str
    model_config = ConfigDict(from_attributes=True)


# ── Approvals ─────────────────────────────────────────────

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


# ── Chat & AI Buyer ───────────────────────────────────────

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
    recommendations: List[dict] = []
    cart: Optional[dict] = None
    order: Optional[dict] = None
    approval: Optional[dict] = None
    actions_taken: List[dict] = []
    decision_explanation: Optional[dict] = None

class BuyerSearchRequest(BaseModel):
    query: str
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


# ── Negotiation & Pricing Simulator ───────────────────────

class NegotiationProposalRequest(BaseModel):
    product_id: str
    requested_price: float
    merchant_id: str = "merchant_001"
    agent_id: str = "ShoppingBot"

class NegotiationProposalResponse(BaseModel):
    product_id: str
    product_name: str
    current_price: float
    requested_price: float
    max_allowed_discount: float
    max_discount_percentage: float
    minimum_margin_price: float
    final_offer: float
    discount_granted_percentage: float
    status: str  # ACCEPTED, COUNTER_OFFER, REJECTED
    reason: str
    currency: str = "INR"

class PricingSimulationRequest(BaseModel):
    product_id: str
    merchant_id: str = "merchant_001"
    competitor_price_adjustment: Optional[float] = 0.0
    demand_multiplier: Optional[float] = 1.0

class PricingSimulationResponse(BaseModel):
    is_simulation: bool = True
    product_id: str
    product_name: str
    current_price: float
    suggested_price: float
    price_change_percentage: float
    stock_level: int
    weekly_sales_velocity: float
    elasticity_score: float
    estimated_revenue_impact: float
    reasons: List[str]
    disclaimer: str = "Simulation and proposal only — live pricing is unchanged until merchant approval."


# ── Inventory Agent ───────────────────────────────────────

class InventoryItemIntelligence(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: float
    stock: int
    weekly_sales: int
    sales_velocity_daily: float
    estimated_days_remaining: int
    stockout_risk: str  # HIGH, MEDIUM, LOW
    overstock_risk: str  # HIGH, MEDIUM, LOW
    recommendation: str
    suggested_action: str

class InventoryIntelligenceResponse(BaseModel):
    merchant_id: str
    total_products: int
    high_stockout_items: List[InventoryItemIntelligence] = []
    overstock_items: List[InventoryItemIntelligence] = []
    all_inventory: List[InventoryItemIntelligence] = []


# ── Cart Optimizer ────────────────────────────────────────

class CartOptimizerRequest(BaseModel):
    cart_id: str
    mode: str = "BEST_VALUE"  # MINIMUM_PRICE, BEST_VALUE, BEST_QUALITY, MAXIMUM_SAVING

class CartOptimizationSuggestion(BaseModel):
    action: str  # REPLACE, ADD_ACCESSORY, REMOVE
    original_product_id: Optional[str] = None
    original_product_name: Optional[str] = None
    suggested_product_id: str
    suggested_product_name: str
    price_difference: float
    reason: str

class CartOptimizerResponse(BaseModel):
    cart_id: str
    mode: str
    current_total: float
    optimized_total: float
    savings: float
    suggestions: List[CartOptimizationSuggestion] = []
    status: str = "PROPOSED"
    disclaimer: str = "Optimization requires customer confirmation before modifying cart."

class ApplyOptimizationRequest(BaseModel):
    cart_id: str
    mode: str


# ── Business What-If Simulator ────────────────────────────

class BusinessSimulationRequest(BaseModel):
    merchant_id: str = "merchant_001"
    discount_percentage: float = 10.0
    inventory_increase_percentage: float = 0.0
    price_adjustment_percentage: float = 0.0
    promoted_category: Optional[str] = None

class BusinessSimulationResponse(BaseModel):
    is_simulation: bool = True
    parameters: dict
    baseline_revenue: float
    estimated_revenue: float
    revenue_delta_percentage: float
    baseline_order_volume: int
    estimated_order_volume: int
    order_volume_delta_percentage: float
    estimated_margin_percentage: float
    confidence_level: str = "HIGH"
    insights: List[str]
    disclaimer: str = "SIMULATION ESTIMATE ONLY — not actual accounting revenue."


# ── AI A/B Testing ────────────────────────────────────────

class ExperimentVariantRead(BaseModel):
    id: str
    name: str
    price: float
    views: int
    orders: int
    revenue: float
    conversion_rate: float
    aov: float
    model_config = ConfigDict(from_attributes=True)

class ExperimentRead(BaseModel):
    id: str
    merchant_id: str
    product_id: Optional[str] = None
    name: str
    hypothesis: str
    status: str
    ai_recommendation: str
    variants: List[ExperimentVariantRead] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ExperimentCreate(BaseModel):
    merchant_id: str = "merchant_001"
    product_id: str
    name: str
    hypothesis: str
    variant_a_price: float
    variant_b_price: float


# ── Refunds ───────────────────────────────────────────────

class RefundCreate(BaseModel):
    order_id: str
    amount: float
    reason: str = "Customer requested cancellation"
    merchant_id: str = "merchant_001"
    user_id: str = "demo_user"

class RefundDecisionRequest(BaseModel):
    status: str  # APPROVED or REJECTED
    approved_by: str = "merchant_admin"
    decision_reason: Optional[str] = None

class RefundRead(BaseModel):
    id: str
    order_id: str
    payment_id: Optional[str] = None
    merchant_id: str
    user_id: str
    amount: float
    currency: str
    reason: str
    status: str
    risk_level: str
    risk_score: int
    approval_id: Optional[str] = None
    approved_by: Optional[str] = None
    decision_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# ── Customer Memory / Preferences ─────────────────────────

class CustomerPreferenceRead(BaseModel):
    id: str
    user_id: str
    preferred_categories: List[str] = []
    preferred_brands: List[str] = []
    preferred_colors: List[str] = []
    budget_min: float = 1000.0
    budget_max: float = 5000.0
    notes: str = ""
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CustomerPreferenceUpdate(BaseModel):
    preferred_categories: Optional[List[str]] = None
    preferred_brands: Optional[List[str]] = None
    preferred_colors: Optional[List[str]] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    notes: Optional[str] = None


# ── Customer Support Agent ────────────────────────────────

class SupportQueryRequest(BaseModel):
    query: str
    user_id: str = "demo_user"
    order_id: Optional[str] = None
    merchant_id: str = "merchant_001"

class SupportQueryResponse(BaseModel):
    answer: str
    query: str
    intent: str  # ORDER_STATUS, PAYMENT_STATUS, REFUND_STATUS, CANCEL_REQUEST, FAQ
    order_details: Optional[dict] = None
    payment_details: Optional[dict] = None
    refund_details: Optional[dict] = None
    suggested_actions: List[str] = []


# ── Agent-to-Agent Commerce ───────────────────────────────

class A2ACommerceRequest(BaseModel):
    customer_agent_goal: str = "Buy the best value running shoes under ₹3000"
    merchant_id: str = "merchant_001"
    user_id: str = "customer_agent_01"

class A2ACommerceResponse(BaseModel):
    steps: List[dict] = []
    final_status: str
    order_id: Optional[str] = None
    amount: float = 0.0
    policy_result: dict = {}
    risk_level: str = "LOW"
    approval_required: bool = False


# ── Safety Certification ──────────────────────────────────

class AgentSafetyCheckItem(BaseModel):
    check_name: str
    passed: bool
    score_points: int
    details: str

class AgentSafetyResponse(BaseModel):
    agent_id: str
    agent_name: str
    safety_score: int
    status: str  # SANDBOX CERTIFIED, REQUIRES_REVISION
    checks: List[AgentSafetyCheckItem] = []
    disclaimer: str = "Sandbox safety verification report based on 10 deterministic governance gates."


# ── Live Events & Observability ───────────────────────────

class LiveEventItem(BaseModel):
    id: str
    timestamp: str
    event_type: str
    actor: str
    summary: str
    details: dict = {}

class ObservabilityMetricsResponse(BaseModel):
    avg_agent_response_ms: int = 240
    avg_tool_latency_ms: int = 45
    avg_payment_latency_ms: int = 320
    avg_webhook_latency_ms: int = 85
    llm_requests_count: int = 142
    total_tokens_used: int = 68400
    estimated_ai_cost_inr: float = 4.25
    ai_assisted_revenue_inr: float = 84990.0
    ai_roi_percentage: float = 19997.0
    cost_disclaimer: str = "ESTIMATED AI COST based on token usage rate; not live billing API data."


# ── MCP & Generic Error ───────────────────────────────────

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

class CopilotQueryRequest(BaseModel):
    query: str
    merchant_id: str = "merchant_001"

class CopilotQueryResponse(BaseModel):
    answer: str
    metrics_used: dict
    suggested_actions: List[str]
    proposed_campaign: Optional[dict] = None

class ErrorDetails(BaseModel):
    code: str
    message: str
    details: dict = {}

class ErrorResponse(BaseModel):
    error: ErrorDetails
