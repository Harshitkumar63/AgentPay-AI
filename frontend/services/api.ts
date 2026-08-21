// AgentPay AI — API client service

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(error?.error?.message || error?.detail?.error?.message || res.statusText);
  }
  return res.json();
}

// ── Health ──
export const getHealth = () => fetchAPI<{ status: string; demo_mode: boolean }>('/health');

// ── Products ──
export const getProducts = (merchantId?: string) =>
  fetchAPI<import('@/types').Product[]>(`/api/products${merchantId ? `?merchant_id=${merchantId}` : ''}`);

export const getProduct = (id: string) =>
  fetchAPI<import('@/types').Product>(`/api/products/${id}`);

export const getCatalog = (merchantId = 'merchant_001') =>
  fetchAPI<{ merchant: Record<string, string>; products: import('@/types').Product[]; total_products: number }>(
    `/api/agent/catalog?merchant_id=${merchantId}`
  );

// ── Cart ──
export const createCart = (userId: string, merchantId: string) =>
  fetchAPI<import('@/types').Cart>('/api/cart', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, merchant_id: merchantId }),
  });

export const getCart = (cartId: string) =>
  fetchAPI<import('@/types').Cart>(`/api/cart/${cartId}`);

export const addToCart = (cartId: string, productId: string, quantity = 1) =>
  fetchAPI<import('@/types').Cart>(`/api/cart/${cartId}/items`, {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, quantity }),
  });

export const removeFromCart = (cartId: string, productId: string) =>
  fetchAPI<import('@/types').Cart>(`/api/cart/${cartId}/items/${productId}`, { method: 'DELETE' });

// ── Orders ──
export const createOrder = (data: {
  cart_id: string;
  user_id: string;
  merchant_id: string;
  idempotency_key?: string;
  order_type?: string;
}) =>
  fetchAPI<{ order: import('@/types').Order; status: string; requires_approval: boolean; policy: Record<string, unknown> }>(
    '/api/orders',
    { method: 'POST', body: JSON.stringify(data) }
  );

export const getOrders = (merchantId?: string) =>
  fetchAPI<import('@/types').Order[]>(`/api/orders${merchantId ? `?merchant_id=${merchantId}` : ''}`);

export const getOrder = (id: string) =>
  fetchAPI<import('@/types').Order>(`/api/orders/${id}`);

// ── Payments ──
export const createPayment = (orderId: string) =>
  fetchAPI<import('@/types').PaymentData>('/api/payments/create', {
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

export const getPaymentStatus = (orderId: string) =>
  fetchAPI<Record<string, unknown>>(`/api/payments/${orderId}`);

// ── Analytics ──
export const getRevenueAnalytics = (merchantId = 'merchant_001', days = 30) =>
  fetchAPI<import('@/types').RevenueAnalytics>(`/api/analytics/revenue?merchant_id=${merchantId}&days=${days}`);

export const getProductAnalytics = (merchantId = 'merchant_001') =>
  fetchAPI<Record<string, unknown>[]>(`/api/analytics/products?merchant_id=${merchantId}`);

export const getGrowthRecommendations = (merchantId = 'merchant_001') =>
  fetchAPI<import('@/types').GrowthRecommendation[]>(`/api/analytics/ai?merchant_id=${merchantId}`);

// ── Agent ──
export const sendChatMessage = (data: {
  message: string;
  session_id?: string;
  user_id?: string;
  merchant_id?: string;
  cart_id?: string | null;
}) =>
  fetchAPI<import('@/types').ChatResponse>('/api/agent/chat', {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const getGrowthAnalysis = (merchantId = 'merchant_001') =>
  fetchAPI<Record<string, unknown>>(`/api/agent/growth?merchant_id=${merchantId}`);

// ── Policies ──
export const getPolicies = (merchantId = 'merchant_001') =>
  fetchAPI<import('@/types').Policy>(`/api/policies?merchant_id=${merchantId}`);

export const updatePolicies = (merchantId: string, data: Partial<import('@/types').Policy>) =>
  fetchAPI<import('@/types').Policy>(`/api/policies?merchant_id=${merchantId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });

// ── Audit ──
export const getAuditLogs = (limit = 50) =>
  fetchAPI<import('@/types').AuditLog[]>(`/api/audit?limit=${limit}`);

export const getAuditLog = (id: string) =>
  fetchAPI<import('@/types').AuditLog>(`/api/audit/${id}`);

export const getAgentActions = (sessionId?: string, limit = 50) =>
  fetchAPI<import('@/types').AgentAction[]>(
    `/api/agent-actions?limit=${limit}${sessionId ? `&session_id=${sessionId}` : ''}`
  );
