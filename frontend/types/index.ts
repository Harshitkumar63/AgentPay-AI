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
  spent_today: number;
  remaining_daily_budget: number;
}

export interface AgentTrust {
  id: string;
  agent_id: string;
  trust_score: number;
  successful_transactions: number;
  failed_payments: number;
  policy_violations: number;
  duplicate_requests: number;
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
