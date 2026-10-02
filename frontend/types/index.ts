// AgentPay AI — TypeScript types for all entities

export interface Product {
  id: string;
  merchant_id: string;
  name: string;
  slug: string;
  description: string;
  category: string;
  price: number;
  currency: string;
  stock: number;
  active: boolean;
  image_url: string;
  tags: string[];
  metadata_extra?: Record<string, any>;
  available?: boolean;
  recommendation_score?: number;
  created_at?: string;
  updated_at?: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  subtotal: number;
}

export interface Cart {
  id: string;
  user_id: string;
  merchant_id: string;
  status: string;
  items: CartItem[];
  subtotal: number;
  total: number;
  item_count?: number;
}

export interface TimelineEvent {
  step: string;
  status: string;
  timestamp: string;
  actor: string;
  [key: string]: any;
}

export interface Order {
  id: string;
  merchant_id: string;
  user_id: string;
  cart_id: string | null;
  agent_id?: string | null;
  agent_session_id?: string | null;
  approval_id?: string | null;
  razorpay_order_id: string | null;
  amount: number;
  currency: string;
  status: string;
  payment_status: string;
  receipt: string | null;
  idempotency_key?: string | null;
  order_type: string;
  timeline?: TimelineEvent[];
  decision_factors?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface Payment {
  id: string;
  order_id: string;
  razorpay_payment_id: string | null;
  amount: number;
  currency: string;
  status: string;
  method: string | null;
  error_code: string | null;
  error_description: string | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  actor_type: string;
  actor_id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  amount: number | null;
  currency: string | null;
  reason: string | null;
  policy_result: string | null;
  approval_status: string | null;
  result: string | null;
  metadata_extra: Record<string, any>;
  created_at: string;
}

export interface WebhookEvent {
  id: string;
  event_id: string | null;
  event_type: string;
  order_id: string | null;
  payment_id: string | null;
  status: string;
  payload_summary?: Record<string, any>;
  error_message: string | null;
  retry_count: number;
  created_at: string;
}

export interface AgentAction {
  id: string;
  session_id: string;
  request_id?: string | null;
  tool_call_id?: string | null;
  sequence_number?: number;
  action: string;
  tool_name: string;
  event_type?: string;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
  status: string;
  error_message: string | null;
  duration_ms: number | null;
  created_at: string;
}

export interface Policy {
  id: string;
  merchant_id: string;
  max_purchase_amount: number;
  max_discount_percentage: number;
  approval_required: boolean;
  auto_refund_enabled: boolean;
  allowed_actions: string[];
  created_at?: string;
  updated_at?: string;
}

export interface PolicyCheckResult {
  allowed: boolean;
  policy_id?: string;
  risk_level: string;
  risk_score: number;
  requires_approval: boolean;
  reason: string;
  details: Record<string, any>;
}

export interface PolicySimulation {
  simulation: boolean;
  input: {
    merchant_id: string;
    amount: number;
    discount_percentage: number;
    action: string;
    agent_id?: string;
  };
  decision: PolicyCheckResult;
}

export interface AgentBudget {
  id: string;
  agent_id: string;
  merchant_id: string;
  daily_limit: number;
  per_transaction_limit: number;
  hourly_limit?: number;
  spent_today: number;
  spent_this_hour?: number;
  remaining_daily_budget: number;
  remaining_hourly_budget?: number;
}

export interface AgentTrust {
  id: string;
  agent_id: string;
  trust_score: number;
  successful_transactions: number;
  failed_payments: number;
  policy_violations: number;
  duplicate_requests: number;
  velocity_violations?: number;
  approval_rate: number;
  risk_tier: string;
  signals?: Record<string, any>;
  disclaimer?: string;
}

export interface Approval {
  id: string;
  agent_session_id?: string | null;
  order_id?: string | null;
  merchant_id: string;
  user_id: string;
  action: string;
  amount: number;
  currency: string;
  risk_level: string;
  risk_score: number;
  policy_result: Record<string, any>;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
  decision_reason?: string | null;
  approved_by?: string | null;
  created_at: string;
  expires_at: string;
  decided_at?: string | null;
}

export interface RecommendationAnalytics {
  recommendations: {
    shown: number;
    clicked: number;
    added: number;
    purchased: number;
    ctr: number;
    conversion_rate: number;
    revenue: number;
  };
  upsell: {
    shown: number;
    clicked: number;
    added: number;
    purchased: number;
    ctr: number;
    conversion_rate: number;
    revenue: number;
  };
  cross_sell: {
    shown: number;
    clicked: number;
    added: number;
    purchased: number;
    ctr: number;
    conversion_rate: number;
    revenue: number;
  };
}

export interface RevenueAnalytics {
  total_revenue: number;
  total_orders: number;
  successful_orders: number;
  average_order_value: number;
  conversion_rate: number;
  ai_assisted_revenue: number;
  upsell_revenue: number;
  cross_sell_revenue: number;
  failed_payments_count?: number;
  blocked_actions_count?: number;
  period: string;
}

export interface GrowthRecommendation {
  type: string;
  title: string;
  description: string;
  evidence: string;
  recommended_action: string;
  estimated_opportunity: number;
  actual_revenue_to_date?: number;
  products: { id: string; name: string; price: number }[];
}

export interface AgentStep {
  sequence?: number;
  step?: number;
  event_type?: string;
  tool: string;
  input: Record<string, any>;
  output_summary: string;
  status: string;
  duration_ms?: number;
  timestamp?: number;
  request_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  products: Product[];
  cart: Cart | null;
  cart_id: string | null;
  actions: { type: string; status: string }[];
  requires_confirmation: boolean;
  confirmation_data: {
    type: string;
    order: Order;
    policy: PolicyCheckResult | Record<string, any>;
    approval?: { id: string; status: string; expires_at: string } | null;
    amount: number;
    message: string;
  } | null;
  agent_steps: AgentStep[];
  explanation?: {
    title: string;
    decision: string;
    factors: string[];
    alternatives_not_selected?: string[];
  } | null;
  demo_mode: boolean;
  limit_reached?: boolean;
}

export interface PaymentData {
  payment_id: string;
  order_id: string;
  razorpay_order_id: string;
  razorpay_key_id: string;
  amount: number;
  currency: string;
  receipt: string;
  demo: boolean;
}

export interface CopilotResponse {
  answer: string;
  metrics_used: Record<string, any>;
  suggested_actions: string[];
  proposed_campaign?: CampaignProposal | null;
}

export interface CampaignProposal {
  id: string;
  merchant_id?: string;
  product_id: string;
  product_name: string;
  title: string;
  description?: string;
  target_audience?: string;
  discount_percentage: number;
  budget: number;
  duration_days: number;
  estimated_opportunity: number;
  evidence?: string;
  risk_level?: string;
  status: string;
  created_at?: string;
  activated_at?: string | null;
}

export interface DecisionReplayData {
  order_id: string;
  order_type: string;
  amount: number;
  currency: string;
  status: string;
  payment_status: string;
  stages: {
    sequence: number;
    title: string;
    status: string;
    summary: string;
    details?: any;
    timestamp: string;
  }[];
  timeline: TimelineEvent[];
  decision_factors: {
    title?: string;
    decision?: string;
    factors?: string[];
    alternatives_not_selected?: string[];
  };
  approval?: Record<string, any> | null;
  payment?: Record<string, any> | null;
  audit_logs: {
    id: string;
    action: string;
    actor: string;
    actor_type: string;
    result: string;
    timestamp: string;
  }[];
}

// ── Multi-Agent Registry ──

export interface AgentRegistryItem {
  id: string;
  name: string;
  description: string;
  role: string;
  status: "ACTIVE" | "PAUSED" | "DISABLED" | "SUSPENDED";
  permissions: string[];
  daily_budget: number;
  per_transaction_limit: number;
  hourly_limit: number;
  trust_score: number;
  risk_level: string;
  circuit_breaker_tripped: boolean;
  circuit_breaker_reason?: string | null;
  failed_payment_count: number;
  is_active: boolean;
  created_at: string;
  last_activity: string;
}

export interface AgentSafetyCheck {
  check_name: string;
  passed: boolean;
  score_points: number;
  details: string;
}

export interface AgentSafetyReport {
  agent_id: string;
  agent_name: string;
  safety_score: number;
  status: string;
  checks: AgentSafetyCheck[];
  disclaimer: string;
}

// ── Negotiation ──

export interface NegotiationProposal {
  product_id: string;
  product_name: string;
  current_price: number;
  requested_price: number;
  max_allowed_discount: number;
  max_discount_percentage: number;
  minimum_margin_price: number;
  final_offer: number;
  discount_granted_percentage: number;
  status: "ACCEPTED" | "COUNTER_OFFER" | "REJECTED";
  reason: string;
  currency: string;
}

// ── Dynamic Pricing ──

export interface PricingSimulation {
  is_simulation: boolean;
  product_id: string;
  product_name: string;
  current_price: number;
  suggested_price: number;
  price_change_percentage: number;
  stock_level: number;
  weekly_sales_velocity: number;
  elasticity_score: number;
  estimated_revenue_impact: number;
  reasons: string[];
  disclaimer: string;
}

// ── Inventory Intelligence ──

export interface InventoryItemIntelligence {
  product_id: string;
  product_name: string;
  category: string;
  price: number;
  stock: number;
  weekly_sales: number;
  sales_velocity_daily: number;
  estimated_days_remaining: number;
  stockout_risk: "HIGH" | "MEDIUM" | "LOW";
  overstock_risk: "HIGH" | "MEDIUM" | "LOW";
  recommendation: string;
  suggested_action: string;
}

export interface InventoryIntelligence {
  merchant_id: string;
  total_products: number;
  high_stockout_items: InventoryItemIntelligence[];
  overstock_items: InventoryItemIntelligence[];
  all_inventory: InventoryItemIntelligence[];
}

// ── Cart Optimizer ──

export interface CartOptimizationSuggestion {
  action: "REPLACE" | "ADD_ACCESSORY" | "REMOVE";
  original_product_id?: string;
  original_product_name?: string;
  suggested_product_id: string;
  suggested_product_name: string;
  price_difference: number;
  reason: string;
}

export interface CartOptimizerProposal {
  cart_id: string;
  mode: string;
  current_total: number;
  optimized_total: number;
  savings: number;
  suggestions: CartOptimizationSuggestion[];
  status: string;
  disclaimer: string;
}

// ── What-If Simulator ──

export interface BusinessSimulation {
  is_simulation: boolean;
  parameters: {
    discount_percentage: number;
    inventory_increase_percentage: number;
    price_adjustment_percentage: number;
    promoted_category?: string;
  };
  baseline_revenue: number;
  estimated_revenue: number;
  revenue_delta_percentage: number;
  baseline_order_volume: number;
  estimated_order_volume: number;
  order_volume_delta_percentage: number;
  estimated_margin_percentage: number;
  confidence_level: string;
  insights: string[];
  disclaimer: string;
}

// ── AI A/B Testing ──

export interface ExperimentVariant {
  id: string;
  name: string;
  price: number;
  views: number;
  orders: number;
  revenue: number;
  conversion_rate: number;
  aov: number;
}

export interface Experiment {
  id: string;
  merchant_id: string;
  product_id?: string;
  name: string;
  hypothesis: string;
  status: string;
  ai_recommendation: string;
  variants: ExperimentVariant[];
  created_at: string;
}

// ── Refunds ──

export interface Refund {
  id: string;
  order_id: string;
  payment_id?: string | null;
  merchant_id: string;
  user_id: string;
  amount: number;
  currency: string;
  reason: string;
  status: string;
  risk_level: string;
  risk_score: number;
  approval_id?: string | null;
  approved_by?: string | null;
  decision_reason?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

// ── Customer Memory ──

export interface CustomerPreference {
  id: string;
  user_id: string;
  preferred_categories: string[];
  preferred_brands: string[];
  preferred_colors: string[];
  budget_min: number;
  budget_max: number;
  notes: string;
  updated_at: string;
}

// ── Support ──

export interface SupportResponse {
  answer: string;
  query: string;
  intent: string;
  order_details?: Record<string, any> | null;
  payment_details?: Record<string, any> | null;
  refund_details?: Record<string, any> | null;
  suggested_actions: string[];
}

// ── Observability ──

export interface ObservabilityMetrics {
  avg_agent_response_ms: number;
  avg_tool_latency_ms: number;
  avg_payment_latency_ms: number;
  avg_webhook_latency_ms: number;
  llm_requests_count: number;
  total_tokens_used: number;
  estimated_ai_cost_inr: number;
  ai_assisted_revenue_inr: number;
  ai_roi_percentage: number;
  cost_disclaimer: string;
}

export interface LiveEventItem {
  id: string;
  timestamp: string;
  event_type: string;
  actor: string;
  actor_type?: string;
  summary: string;
  amount?: number | null;
  currency?: string;
  policy_result?: string | null;
  approval_status?: string | null;
  details?: Record<string, any>;
}
