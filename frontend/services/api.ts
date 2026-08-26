// AgentPay AI — API Client Service

import {
  Product,
  Cart,
  Order,
  PaymentData,
  RevenueAnalytics,
  GrowthRecommendation,
  ChatResponse,
  Policy,
  PolicySimulation,
  AuditLog,
  AgentAction,
  WebhookEvent,
  CopilotResponse,
  AgentBudget,
  AgentTrust,
  Approval,
  RecommendationAnalytics,
  CampaignProposal,
  DecisionReplayData,
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${endpoint}`, {
      headers: { 'Content-Type': 'application/json', ...options?.headers },
      ...options,
    });
  } catch (err: any) {
    console.error(`[API] Network error fetching ${API_URL}${endpoint}:`, err);
    throw new Error(
      `Failed to connect to backend server at ${API_URL}. Please ensure the FastAPI backend is running (port 8000).`
    );
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(error?.error?.message || error?.detail?.message || error?.detail || error?.message || res.statusText);
  }
  return res.json();
}

// ── Health ──
export const getHealth = () =>
  fetchAPI<{ status: string; service: string; demo_mode: boolean; ai_configured: boolean; razorpay_configured: boolean }>(
    '/health'
  );

// ── Products ──
export const getProducts = (merchantId?: string) =>
  fetchAPI<Product[]>(`/api/products${merchantId ? `?merchant_id=${merchantId}` : ''}`);

export const getProduct = (id: string) => fetchAPI<Product>(`/api/products/${id}`);

export const getCatalog = (merchantId = 'merchant_001') =>
  fetchAPI<{ merchant: Record<string, string>; products: Product[]; total_products: number }>(
    `/api/agent/v1/catalog?merchant_id=${merchantId}`
  );

// ── Cart ──
export const createCart = (userId = 'demo_user', merchantId = 'merchant_001') =>
  fetchAPI<Cart>('/api/cart', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, merchant_id: merchantId }),
  });

export const getCart = (cartId: string) => fetchAPI<Cart>(`/api/cart/${cartId}`);

export const addToCart = (cartId: string, productId: string, quantity = 1) =>
  fetchAPI<Cart>(`/api/cart/${cartId}/items`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  });

export const removeFromCart = (cartId: string, productId: string) =>
  fetchAPI<Cart>(`/api/cart/${cartId}/items/${productId}`, { method: 'DELETE' });

// ── Orders ──
export const createOrder = (data: {
  cart_id: string;
  user_id: string;
  merchant_id: string;
  idempotency_key?: string;
  order_type?: string;
}) =>
  fetchAPI<{
    order: Order;
    status: string;
    requires_approval: boolean;
    approval?: { id: string; status: string; expires_at: string };
    policy: Record<string, any>;
    message?: string;
  }>('/api/orders', { method: 'POST', body: JSON.stringify(data) });

export const getOrders = (merchantId?: string) =>
  fetchAPI<Order[]>(`/api/orders${merchantId ? `?merchant_id=${merchantId}` : ''}`);

export const getOrder = (id: string) => fetchAPI<Order>(`/api/orders/${id}`);

export const getOrderTimeline = (id: string) =>
  fetchAPI<{ order_id: string; status: string; payment_status: string; timeline: any[] }>(
    `/api/orders/${id}/timeline`
  );

export const getDecisionReplay = (id: string) =>
  fetchAPI<DecisionReplayData>(`/api/orders/${id}/decision-replay`);

// ── Payments ──
export const createPayment = (orderId: string) =>
  fetchAPI<PaymentData>('/api/payments/create', {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId }),
  });

export const verifyPayment = (data: {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}) =>
  fetchAPI<{ success: boolean; order_id: string; payment_status: string; order_status: string }>(
    '/api/payments/verify',
    {
      method: 'POST',
      body: JSON.stringify(data),
    }
  );

export const getPaymentStatus = (orderId: string) =>
  fetchAPI<Record<string, any>>(`/api/payments/${orderId}`);

// ── Analytics, Recommendations & Growth ──
export const getRevenueAnalytics = (merchantId = 'merchant_001', days = 30) =>
  fetchAPI<RevenueAnalytics>(`/api/analytics/revenue?merchant_id=${merchantId}&days=${days}`);

export const getProductAnalytics = (merchantId = 'merchant_001') =>
  fetchAPI<Record<string, any>[]>(`/api/analytics/products?merchant_id=${merchantId}`);

export const getGrowthRecommendations = (merchantId = 'merchant_001') =>
  fetchAPI<GrowthRecommendation[]>(`/api/analytics/ai?merchant_id=${merchantId}`);

export const getRecommendationAnalytics = (merchantId = 'merchant_001') =>
  fetchAPI<RecommendationAnalytics>(`/api/analytics/recommendations?merchant_id=${merchantId}`);

export const queryMerchantCopilot = (query: string, merchantId = 'merchant_001') =>
  fetchAPI<CopilotResponse>('/api/analytics/copilot', {
    method: 'POST',
    body: JSON.stringify({ query, merchant_id: merchantId }),
  });

// ── AI Campaigns ──
export const getCampaigns = (merchantId = 'merchant_001') =>
  fetchAPI<CampaignProposal[]>(`/api/campaigns?merchant_id=${merchantId}`);

export const proposeCampaign = (data: {
  product_id: string;
  title: string;
  discount_percentage: number;
  budget: number;
  duration_days: number;
  target_audience: string;
  merchant_id?: string;
}) =>
  fetchAPI<CampaignProposal>('/api/campaigns/propose', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const activateCampaign = (campaignId: string, approvedBy = 'merchant_admin') =>
  fetchAPI<{ success: boolean; campaign_id: string; status: string; message: string }>(
    `/api/campaigns/${campaignId}/activate?approved_by=${approvedBy}`,
    { method: 'POST' }
  );

// ── Agent ──
export const sendChatMessage = (data: {
  message: string;
  session_id?: string;
  user_id?: string;
  merchant_id?: string;
  cart_id?: string | null;
}) =>
  fetchAPI<ChatResponse>('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getAgentActions = (sessionId?: string, limit = 50) =>
  fetchAPI<AgentAction[]>(`/api/agent-actions?limit=${limit}${sessionId ? `&session_id=${sessionId}` : ''}`);

// ── Agent Budget & Trust ──
export const getAgentBudget = (agentId = 'default_agent', merchantId = 'merchant_001') =>
  fetchAPI<AgentBudget>(`/api/agent/budget?agent_id=${agentId}&merchant_id=${merchantId}`);

export const updateAgentBudget = (
  limits: { daily_limit?: number; per_transaction_limit?: number },
  agentId = 'default_agent',
  merchantId = 'merchant_001'
) =>
  fetchAPI<AgentBudget>(`/api/agent/budget?agent_id=${agentId}&merchant_id=${merchantId}`, {
    method: 'PUT',
    body: JSON.stringify(limits),
  });

export const getAgentTrust = (agentId = 'default_agent') =>
  fetchAPI<AgentTrust>(`/api/agent/trust?agent_id=${agentId}`);

// ── Human Approvals ──
export const getApprovals = (merchantId = 'merchant_001', status?: string) =>
  fetchAPI<Approval[]>(`/api/approvals?merchant_id=${merchantId}${status ? `&status=${status}` : ''}`);

export const getApproval = (id: string) => fetchAPI<Approval>(`/api/approvals/${id}`);

export const decideApproval = (id: string, status: 'APPROVED' | 'REJECTED', reason?: string) =>
  fetchAPI<{ success: boolean; approval_id: string; status: string; order_id?: string }>(
    `/api/approvals/${id}/decide`,
    {
      method: 'POST',
      body: JSON.stringify({ status, approved_by: 'merchant_admin', reason }),
    }
  );

// ── Policies & Simulator ──
export const getPolicies = (merchantId = 'merchant_001') =>
  fetchAPI<Policy>(`/api/policies?merchant_id=${merchantId}`);

export const updatePolicies = (merchantId: string, data: Partial<Policy>) =>
  fetchAPI<Policy>(`/api/policies?merchant_id=${merchantId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

export const simulatePolicy = (data: {
  amount: number;
  discount_percentage?: number;
  action?: string;
  merchant_id?: string;
  agent_id?: string;
}) =>
  fetchAPI<PolicySimulation>('/api/policies/simulate', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// ── Webhooks & Monitor ──
export const getWebhookEvents = (limit = 50, status?: string) =>
  fetchAPI<WebhookEvent[]>(`/api/webhooks?limit=${limit}${status ? `&status=${status}` : ''}`);

export const simulateWebhook = (eventType: string, razorpayOrderId?: string, razorpayPaymentId?: string) =>
  fetchAPI<{ status: string; event_id: string; event: string }>(
    `/api/webhooks/simulate?event_type=${eventType}${razorpayOrderId ? `&razorpay_order_id=${razorpayOrderId}` : ''}${
      razorpayPaymentId ? `&razorpay_payment_id=${razorpayPaymentId}` : ''
    }`,
    { method: 'POST' }
  );

// ── Audit ──
export const getAuditLogs = (limit = 50, action?: string) =>
  fetchAPI<AuditLog[]>(`/api/audit?limit=${limit}${action ? `&action=${action}` : ''}`);

export const getAuditLog = (id: string) => fetchAPI<AuditLog>(`/api/audit/${id}`);

// ── AI Buyer API (v1) Direct ──
export const getBuyerTools = () => fetchAPI<Record<string, any>>('/api/agent/v1/tools');

export const buyerSearch = (query: string, maxPrice?: number) =>
  fetchAPI<Record<string, any>>('/api/agent/v1/search', {
    method: 'POST',
    body: JSON.stringify({ query, max_price: maxPrice }),
  });

export const buyerCreateCart = (userId = 'ai_buyer_agent') =>
  fetchAPI<Cart>('/api/agent/v1/cart', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId }),
  });

export const buyerAddToCart = (cartId: string, productId: string, quantity = 1) =>
  fetchAPI<Cart>(`/api/agent/v1/cart/${cartId}/items`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  });

export const buyerCheckout = (cartId: string, idempotencyKey?: string) =>
  fetchAPI<{
    status: string;
    order: Order;
    requires_approval: boolean;
    approval?: any;
    policy: Record<string, any>;
    payment?: any;
  }>('/api/agent/v1/checkout', {
    method: 'POST',
    body: JSON.stringify({
      cart_id: cartId,
      user_id: 'ai_buyer_agent',
      merchant_id: 'merchant_001',
      idempotency_key: idempotencyKey,
      order_type: 'ai_assisted',
    }),
  });

// ── Model Context Protocol (MCP) ──
export const getMcpTools = () => fetchAPI<Record<string, any>>('/api/mcp/tools');

export const callMcpTool = (toolName: string, args: Record<string, any> = {}) =>
  fetchAPI<{ tool_name: string; result: any; duration_ms: number; status: string }>('/api/mcp/call', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName, arguments: args }),
  });
