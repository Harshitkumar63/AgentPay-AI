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
  metadata_extra: Record<string, unknown>;
  available?: boolean;
  created_at: string;
  updated_at: string;
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

export interface Order {
  id: string;
  merchant_id: string;
  user_id: string;
  cart_id: string | null;
  razorpay_order_id: string | null;
  amount: number;
  currency: string;
  status: string;
  payment_status: string;
  receipt: string | null;
  order_type: string;
  created_at: string;
  updated_at: string;
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
  metadata_extra: Record<string, unknown>;
  created_at: string;
}

export interface AgentAction {
  id: string;
  session_id: string;
  action: string;
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
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
  created_at: string;
  updated_at: string;
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
  period: string;
}

export interface GrowthRecommendation {
  type: string;
  title: string;
  description: string;
  evidence: string;
  recommended_action: string;
  estimated_opportunity: number;
  products: { id: string; name: string; price: number }[];
}

export interface AgentStep {
  step: number;
  tool: string;
  input: Record<string, unknown>;
  output_summary: string;
  status: string;
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
    policy: { allowed: boolean; reason: string; requires_approval: boolean };
    amount: number;
    message: string;
  } | null;
  agent_steps: AgentStep[];
  demo_mode: boolean;
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
