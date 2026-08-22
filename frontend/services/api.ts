// AgentPay AI — API client service

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
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(error?.error?.message || error?.detail?.message || error?.detail || res.statusText);
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
    policy: Record<string, any>;
    message?: string;
  }>('/api/orders', { method: 'POST', body: JSON.stringify(data) });

export const getOrders = (merchantId?: string) =>
  fetchAPI<Order[]>(`/api/orders${merchantId ? `?merchant_id=${merchantId}` : ''}`);

export const getOrder = (id: string) => fetchAPI<Order>(`/api/orders/${id}`);

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
  fetchAPI<{ success: boolean; order_id: string; payment_status: string }>('/api/payments/verify', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getPaymentStatus = (orderId: string) => fetchAPI<Record<string, any>>(`/api/payments/${orderId}`);

// ── Analytics & Growth ──
export const getRevenueAnalytics = (merchantId = 'merchant_001', days = 30) =>
  fetchAPI<RevenueAnalytics>(`/api/analytics/revenue?merchant_id=${merchantId}&days=${days}`);

export const getProductAnalytics = (merchantId = 'merchant_001') =>
  fetchAPI<Record<string, any>[]>(`/api/analytics/products?merchant_id=${merchantId}`);

export const getGrowthRecommendations = (merchantId = 'merchant_001') =>
  fetchAPI<GrowthRecommendation[]>(`/api/analytics/ai?merchant_id=${merchantId}`);

export const queryMerchantCopilot = (query: string, merchantId = 'merchant_001') =>
  fetchAPI<CopilotResponse>('/api/analytics/copilot', {
    method: 'POST',
    body: JSON.stringify({ query, merchant_id: merchantId }),
  });

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
