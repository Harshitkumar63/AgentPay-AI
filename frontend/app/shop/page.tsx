"use client";

import { useState, useRef, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Send, ShoppingCart, Bot, User, Plus, Minus, Trash2,
  Check, X, Shield, Sparkles, ArrowRight, Package
} from "lucide-react";
import { sendChatMessage, createCart, addToCart, removeFromCart, createOrder, createPayment, verifyPayment } from "@/services/api";
import type { ChatResponse, Product, Cart, PaymentData } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  products?: Product[];
  agentSteps?: ChatResponse["agent_steps"];
  confirmation?: ChatResponse["confirmation_data"];
}

export default function ShopPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "👋 Welcome to UrbanCart! I'm your AI shopping assistant. I can help you find products, compare options, and complete purchases. Try asking me:\n\n• \"Find black running shoes under ₹3000\"\n• \"Show me laptops\"\n• \"What accessories go with running shoes?\"\n• \"Compare backpacks\"\n\nWhat are you looking for today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cartId, setCartId] = useState<string | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [showApproval, setShowApproval] = useState(false);
  const [approvalData, setApprovalData] = useState<ChatResponse["confirmation_data"]>(null);
  const [processingPayment, setProcessingPayment] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await sendChatMessage({
        message: userMsg,
        session_id: sessionId || undefined,
        user_id: "demo_user",
        merchant_id: "merchant_001",
        cart_id: cartId,
      });

      setSessionId(res.session_id);
      if (res.cart_id) setCartId(res.cart_id);
      if (res.cart) setCart(res.cart as Cart);

      const assistantMsg: Message = {
        role: "assistant",
        content: res.message,
        products: res.products?.length > 0 ? res.products : undefined,
        agentSteps: res.agent_steps?.length > 0 ? res.agent_steps : undefined,
      };

      if (res.requires_confirmation && res.confirmation_data) {
        assistantMsg.confirmation = res.confirmation_data;
        setApprovalData(res.confirmation_data);
        setShowApproval(true);
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Error: ${errorMessage}. Please try again.` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async (product: Product) => {
    try {
      let currentCartId = cartId;
      if (!currentCartId) {
        const newCart = await createCart("demo_user", "merchant_001");
        currentCartId = newCart.id;
        setCartId(currentCartId);
      }
      const updated = await addToCart(currentCartId, product.id, 1);
      setCart(updated);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `✅ Added **${product.name}** to your cart! Total: ₹${updated.total.toLocaleString("en-IN")}` },
      ]);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Failed to add to cart";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ ${errorMessage}` },
      ]);
    }
  };

  const handleRemoveFromCart = async (productId: string) => {
    if (!cartId) return;
    try {
      const updated = await removeFromCart(cartId, productId);
      setCart(updated);
    } catch (err) {
      console.error("Remove from cart error:", err);
    }
  };

  const handleApproval = async (approved: boolean) => {
    setShowApproval(false);
    if (!approved) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Purchase cancelled. Feel free to browse or modify your cart!" },
      ]);
      return;
    }

    // Process purchase
    setProcessingPayment(true);
    try {
      const orderId = approvalData?.order?.id;
      if (!orderId) throw new Error("No order ID");

      // Create payment
      const paymentData: PaymentData = await createPayment(orderId);

      if (paymentData.demo) {
        // Demo mode — simulate payment
        await verifyPayment({
          razorpay_order_id: paymentData.razorpay_order_id,
          razorpay_payment_id: `pay_demo_${Date.now()}`,
          razorpay_signature: "demo_signature",
        });
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `🎉 **Payment successful!** (DEMO MODE)\n\nOrder ID: ${orderId}\nAmount: ₹${(paymentData.amount / 100).toLocaleString("en-IN")}\nStatus: Captured\n\nYour order has been confirmed. Check the Audit Logs to see the full transaction trail.`,
          },
        ]);
        setCart(null);
        setCartId(null);
      } else {
        // Real Razorpay checkout
        const options = {
          key: paymentData.razorpay_key_id,
          amount: paymentData.amount,
          currency: paymentData.currency,
          name: "UrbanCart",
          description: "Purchase via AgentPay AI",
          order_id: paymentData.razorpay_order_id,
          handler: async function (response: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) {
            try {
              await verifyPayment({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature,
              });
              setMessages((prev) => [
                ...prev,
                {
                  role: "assistant",
                  content: `🎉 **Payment successful!**\n\nPayment ID: ${response.razorpay_payment_id}\nOrder confirmed.`,
                },
              ]);
              setCart(null);
              setCartId(null);
            } catch {
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "❌ Payment verification failed. Please contact support." },
              ]);
            }
          },
          prefill: { name: "Demo User", email: "demo@agentpay.ai" },
          theme: { color: "#6c5ce7" },
        };

        // Load Razorpay script dynamically
        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => {
          const rzp = new (window as unknown as Record<string, unknown> & { Razorpay: new (options: Record<string, unknown>) => { open: () => void } }).Razorpay(options);
          rzp.open();
        };
        document.body.appendChild(script);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Payment failed";
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `❌ **Payment failed:** ${errorMessage}\n\nYour order is saved. You can retry the payment from the Orders page.`,
        },
      ]);
    } finally {
      setProcessingPayment(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header">
        <h1 style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Sparkles size={28} style={{ color: "#6c5ce7" }} /> AI Shop
        </h1>
        <p>Natural language shopping powered by AI agents</p>
      </div>

      <div className="chat-container">
        {/* Chat Area */}
        <div className="chat-main">
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i}>
                <div className={`chat-message ${msg.role === "user" ? "user" : "ai"}`}>
                  <div className={`chat-avatar ${msg.role === "user" ? "user" : "ai"}`}>
                    {msg.role === "user" ? <User size={16} color="white" /> : <Bot size={16} color="white" />}
                  </div>
                  <div className="chat-bubble">
                    {msg.content.split("\n").map((line, j) => (
                      <p key={j} style={{ marginBottom: line ? 4 : 0 }}>
                        {line.replace(/\*\*(.*?)\*\*/g, "$1")}
                      </p>
                    ))}
                  </div>
                </div>

                {/* Agent Steps */}
                {msg.agentSteps && msg.agentSteps.length > 0 && (
                  <div className="agent-steps" style={{ marginLeft: 44, marginBottom: 16 }}>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 6 }}>
                      🔧 Agent Steps:
                    </div>
                    {msg.agentSteps.map((step, k) => (
                      <div key={k} className="agent-step">
                        <div className="agent-step-number">{step.step}</div>
                        <span className="agent-step-tool">{step.tool}</span>
                        <span style={{ color: "var(--text-muted)" }}>{step.output_summary}</span>
                        <span className={`badge ${step.status === "success" ? "badge-success" : "badge-danger"}`} style={{ marginLeft: "auto" }}>
                          {step.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Product Cards */}
                {msg.products && msg.products.length > 0 && (
                  <div className="product-grid" style={{ marginLeft: 44, marginBottom: 16 }}>
                    {msg.products.map((product) => (
                      <div key={product.id} className="product-card">
                        <div className="product-card-header">
                          <h3>{product.name}</h3>
                          <span className="product-price">₹{product.price.toLocaleString("en-IN")}</span>
                        </div>
                        <p>{product.description}</p>
                        <div className="product-tags">
                          {(product.tags || []).slice(0, 4).map((tag) => (
                            <span key={tag} className="product-tag">{tag}</span>
                          ))}
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                          <span className={`badge ${product.stock > 0 ? "badge-success" : "badge-danger"}`}>
                            {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
                          </span>
                        </div>
                        <div className="product-actions">
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleAddToCart(product)}
                            disabled={product.stock <= 0}
                            style={{ flex: 1 }}
                          >
                            <Plus size={14} /> Add to Cart
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-message ai">
                <div className="chat-avatar ai"><Bot size={16} color="white" /></div>
                <div className="chat-bubble" style={{ display: "flex", gap: 4 }}>
                  <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                  <span style={{ color: "var(--text-muted)" }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input-container">
            <input
              className="chat-input"
              placeholder="Ask me anything... e.g., 'Find black running shoes under ₹3000'"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={sendMessage} disabled={loading}>
              <Send size={18} />
            </button>
          </div>
        </div>

        {/* Cart Sidebar */}
        <div className="cart-sidebar">
          <div className="cart-header">
            <ShoppingCart size={18} />
            <span>Cart</span>
            {cart?.items && cart.items.length > 0 && (
              <span className="badge badge-purple" style={{ marginLeft: "auto" }}>{cart.items.length}</span>
            )}
          </div>

          <div className="cart-items">
            {cart?.items && cart.items.length > 0 ? (
              cart.items.map((item) => (
                <div key={item.id} className="cart-item">
                  <div className="cart-item-info">
                    <h4>{item.product_name}</h4>
                    <p>₹{item.unit_price.toLocaleString("en-IN")} × {item.quantity}</p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontWeight: 600 }}>₹{item.subtotal.toLocaleString("en-IN")}</span>
                    <button className="btn-ghost" onClick={() => handleRemoveFromCart(item.product_id)} style={{ padding: 4 }}>
                      <Trash2 size={14} color="var(--danger)" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <ShoppingCart size={32} />
                <h3>Cart is empty</h3>
                <p style={{ fontSize: 13 }}>Ask the AI to find products!</p>
              </div>
            )}
          </div>

          {cart?.items && cart.items.length > 0 && (
            <div className="cart-footer">
              <div className="cart-total">
                <span>Total</span>
                <span>₹{cart.total.toLocaleString("en-IN")}</span>
              </div>
              <button
                className="btn btn-primary"
                style={{ width: "100%" }}
                onClick={() => setInput("Buy these items")}
              >
                <ArrowRight size={16} /> Checkout with AI
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Approval Dialog */}
      {showApproval && approvalData && (
        <div className="approval-overlay">
          <div className="approval-dialog">
            <h2>
              <Shield size={22} style={{ color: "#6c5ce7" }} />
              Purchase Confirmation
            </h2>

            <div className="approval-detail">
              <span className="label">Order ID</span>
              <span>{approvalData.order?.id}</span>
            </div>
            <div className="approval-detail">
              <span className="label">Amount</span>
              <span style={{ fontWeight: 700, fontSize: 18 }}>₹{approvalData.amount?.toLocaleString("en-IN")}</span>
            </div>
            <div className="approval-detail">
              <span className="label">Policy</span>
              <span className={`badge ${approvalData.policy?.allowed ? "badge-success" : "badge-danger"}`}>
                {approvalData.policy?.allowed ? "ALLOWED" : "BLOCKED"}
              </span>
            </div>
            <div className="approval-detail">
              <span className="label">Reason</span>
              <span style={{ fontSize: 13 }}>{approvalData.policy?.reason}</span>
            </div>

            <div style={{ marginTop: 16, padding: 12, background: "var(--success-bg)", borderRadius: "var(--radius-sm)", fontSize: 13 }}>
              ⚡ User approval required before processing payment
            </div>

            <div className="approval-actions">
              <button className="btn btn-secondary" onClick={() => handleApproval(false)} disabled={processingPayment}>
                <X size={16} /> Cancel
              </button>
              <button className="btn btn-success" onClick={() => handleApproval(true)} disabled={processingPayment}>
                {processingPayment ? (
                  <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
                ) : (
                  <Check size={16} />
                )}
                Confirm Purchase
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
