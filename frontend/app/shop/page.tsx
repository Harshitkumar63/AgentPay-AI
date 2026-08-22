"use client";

import { useState, useRef, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Send,
  ShoppingCart,
  Bot,
  User,
  Plus,
  Trash2,
  Check,
  X,
  Shield,
  Sparkles,
  ArrowRight,
  Info,
  Layers,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import {
  sendChatMessage,
  createCart,
  addToCart,
  removeFromCart,
  createPayment,
  verifyPayment,
} from "@/services/api";
import type { ChatResponse, Product, Cart, PaymentData } from "@/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  products?: Product[];
  agentSteps?: ChatResponse["agent_steps"];
  confirmation?: ChatResponse["confirmation_data"];
  explanation?: ChatResponse["explanation"];
}

export default function ShopPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "👋 Welcome to UrbanCart! I am your autonomous AI shopping assistant.\n\nI can discover products from our verified catalog, check live inventory, provide cross-sell recommendations, and execute policy-gated checkouts.\n\nTry asking me:",
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

  const quickPrompts = [
    "Find black running shoes under ₹3000",
    "Show me laptops under ₹50000",
    "What accessories go with running shoes?",
    "Compare running shoes",
    "Buy now",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text?: string) => {
    const msgToSend = text || input;
    if (!msgToSend.trim() || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msgToSend.trim() }]);
    setLoading(true);

    try {
      const res = await sendChatMessage({
        message: msgToSend.trim(),
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
        explanation: res.explanation || undefined,
      };

      if (res.requires_confirmation && res.confirmation_data) {
        assistantMsg.confirmation = res.confirmation_data;
        setApprovalData(res.confirmation_data);
        setShowApproval(true);
      }

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Error: ${err.message || "Failed to process request"}. Please try again.` },
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
        {
          role: "assistant",
          content: `✅ Added **${product.name}** to your cart! Total: ₹${updated.total.toLocaleString("en-IN")}\n\nSay "Buy now" whenever you're ready to proceed to checkout.`,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ ${err.message || "Failed to add to cart"}` },
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
        { role: "assistant", content: "🛑 Purchase authorization cancelled by user. Cart remains preserved." },
      ]);
      return;
    }

    setProcessingPayment(true);
    try {
      const orderId = approvalData?.order?.id;
      if (!orderId) throw new Error("No order ID available");

      const paymentData: PaymentData = await createPayment(orderId);

      if (paymentData.demo) {
        await verifyPayment({
          razorpay_order_id: paymentData.razorpay_order_id,
          razorpay_payment_id: `pay_demo_${Date.now()}`,
          razorpay_signature: "demo_signature",
        });
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `🎉 **Payment Verified & Captured!** (RAZORPAY TEST MODE)\n\n• Order ID: \`${orderId}\`\n• Amount: **₹${(paymentData.amount / 100).toLocaleString("en-IN")}**\n• Status: \`CAPTURED\`\n• Gateway Signature: \`VERIFIED\`\n\nFull immutable transaction ledger recorded in Audit Logs.`,
          },
        ]);
        setCart(null);
        setCartId(null);
      } else {
        const options = {
          key: paymentData.razorpay_key_id,
          amount: paymentData.amount,
          currency: paymentData.currency,
          name: "UrbanCart",
          description: "Purchase via AgentPay AI",
          order_id: paymentData.razorpay_order_id,
          handler: async function (response: any) {
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
                  content: `🎉 **Payment Confirmed & Verified!**\n\nPayment ID: \`${response.razorpay_payment_id}\`\nOrder successfully fulfilled.`,
                },
              ]);
              setCart(null);
              setCartId(null);
            } catch {
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "❌ Payment verification failed. Please check payment logs." },
              ]);
            }
          },
          prefill: { name: "Demo User", email: "demo@agentpay.ai" },
          theme: { color: "#6c5ce7" },
        };

        const script = document.createElement("script");
        script.src = "https://checkout.razorpay.com/v1/checkout.js";
        script.onload = () => {
          const rzp = new (window as any).Razorpay(options);
          rzp.open();
        };
        document.body.appendChild(script);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `❌ **Payment Execution Failed:** ${err.message || "Gateway declined transaction"}\n\nSafe failure event logged in Audit Trail. You may retry checkout.`,
        },
      ]);
    } finally {
      setProcessingPayment(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="text-indigo-400" /> AI Conversational Shop
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Natural language catalog discovery, algorithmic upselling, and policy-gated checkout
          </p>
        </div>
      </div>

      {/* Quick Prompts Bar */}
      <div className="flex flex-wrap gap-2 mb-4">
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(p)}
            className="btn btn-ghost btn-sm text-xs bg-gray-900/60 border border-gray-800 hover:border-indigo-500/50 hover:bg-indigo-950/20"
          >
            {p}
          </button>
        ))}
      </div>

      <div className="chat-container">
        {/* Main Conversation Window */}
        <div className="chat-main">
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className="mb-4">
                <div className={`chat-message ${msg.role === "user" ? "user" : "ai"}`}>
                  <div className={`chat-avatar ${msg.role === "user" ? "user" : "ai"}`}>
                    {msg.role === "user" ? <User size={16} color="white" /> : <Bot size={16} color="white" />}
                  </div>
                  <div className="chat-bubble flex-1">
                    {msg.content.split("\n").map((line, j) => (
                      <p key={j} style={{ marginBottom: line ? 4 : 0 }}>
                        {line}
                      </p>
                    ))}

                    {/* "Why did the AI do this?" (Phase 15) */}
                    {msg.explanation && (
                      <div className="explanation-box">
                        <div className="explanation-title">
                          <Info size={13} />
                          {msg.explanation.title}
                        </div>
                        {msg.explanation.factors?.map((fac, fIdx) => (
                          <div key={fIdx} className="explanation-factor">
                            <CheckCircle2 size={12} className="text-emerald-400 shrink-0" />
                            <span>{fac}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Agent Steps Execution Trace */}
                {msg.agentSteps && msg.agentSteps.length > 0 && (
                  <div className="agent-steps ml-12 mb-3">
                    <div className="text-xs text-gray-400 mb-1 font-semibold flex items-center gap-1">
                      <Layers size={13} className="text-indigo-400" />
                      Autonomous Tool Trace:
                    </div>
                    {msg.agentSteps.map((step, k) => (
                      <div key={k} className="agent-step">
                        <div className="agent-step-number">{step.step}</div>
                        <span className="agent-step-tool font-mono">{step.tool}()</span>
                        <span className="text-xs text-gray-400">{step.output_summary}</span>
                        <span
                          className={`badge text-xs ml-auto ${
                            step.status === "success" ? "badge-success" : "badge-danger"
                          }`}
                        >
                          {step.status}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Product Catalog Cards */}
                {msg.products && msg.products.length > 0 && (
                  <div className="product-grid ml-12 mb-3">
                    {msg.products.map((product) => (
                      <div key={product.id} className="product-card">
                        <div className="product-card-header">
                          <h3>{product.name}</h3>
                          <span className="product-price">₹{product.price.toLocaleString("en-IN")}</span>
                        </div>
                        <p>{product.description}</p>
                        <div className="product-tags">
                          {(product.tags || []).slice(0, 4).map((tag) => (
                            <span key={tag} className="product-tag">
                              {tag}
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center justify-between mb-3 text-xs">
                          <span
                            className={`badge ${
                              product.stock > 0 ? "badge-success" : "badge-danger"
                            }`}
                          >
                            {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
                          </span>
                          <span className="text-gray-400 text-xs">{product.category}</span>
                        </div>
                        <div className="product-actions">
                          <button
                            className="btn btn-primary btn-sm w-full"
                            onClick={() => handleAddToCart(product)}
                            disabled={product.stock <= 0}
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
                <div className="chat-avatar ai">
                  <Bot size={16} color="white" />
                </div>
                <div className="chat-bubble flex items-center gap-2">
                  <span className="spinner w-4 h-4" />
                  <span className="text-xs text-gray-400">Agent reasoning & checking catalog...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <div className="chat-input-container">
            <input
              className="chat-input"
              placeholder="Ask anything... e.g. 'Find black running shoes under ₹3000' or 'Buy it'"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={loading}
            />
            <button className="btn btn-primary" onClick={() => sendMessage()} disabled={loading}>
              <Send size={16} />
            </button>
          </div>
        </div>

        {/* Live Cart Sidebar */}
        <div className="cart-sidebar">
          <div className="cart-header">
            <ShoppingCart size={18} />
            <span>Active Cart</span>
            {cart?.items && cart.items.length > 0 && (
              <span className="badge badge-purple ml-auto">{cart.items.length} items</span>
            )}
          </div>

          <div className="cart-items">
            {cart?.items && cart.items.length > 0 ? (
              cart.items.map((item) => (
                <div key={item.id} className="cart-item">
                  <div className="cart-item-info">
                    <h4>{item.product_name}</h4>
                    <p>
                      ₹{item.unit_price.toLocaleString("en-IN")} × {item.quantity}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">₹{item.subtotal.toLocaleString("en-IN")}</span>
                    <button
                      className="btn-ghost p-1"
                      onClick={() => handleRemoveFromCart(item.product_id)}
                    >
                      <Trash2 size={14} className="text-rose-400" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <ShoppingCart size={32} className="mx-auto opacity-50" />
                <h3>Cart is empty</h3>
                <p className="text-xs">Ask the AI agent to discover and add items.</p>
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
                className="btn btn-primary w-full"
                onClick={() => sendMessage("Buy these items")}
              >
                <ArrowRight size={16} /> Gated AI Checkout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Human Approval Gate Modal (Phase 14) */}
      {showApproval && approvalData && (
        <div className="approval-overlay">
          <div className="approval-dialog">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold flex items-center gap-2 text-indigo-300">
                <Shield size={20} className="text-indigo-400" />
                Human Approval Required
              </h2>
              <span className="risk-pill risk-high">High Risk</span>
            </div>

            <p className="text-xs text-gray-400 mb-3">
              The AI Agent prepared this transaction. Before creating the payment order on Razorpay, your explicit authorization is required.
            </p>

            <div className="space-y-2 py-2 border-y border-gray-800 text-xs">
              <div className="approval-detail">
                <span className="label">Order Reference</span>
                <span className="font-mono">{approvalData.order?.id}</span>
              </div>
              <div className="approval-detail">
                <span className="label">Calculated Amount</span>
                <span className="font-bold text-base text-emerald-400">
                  ₹{approvalData.amount?.toLocaleString("en-IN")}
                </span>
              </div>
              <div className="approval-detail">
                <span className="label">Policy Decision</span>
                <span
                  className={`badge ${
                    approvalData.policy?.allowed ? "badge-success" : "badge-danger"
                  }`}
                >
                  {approvalData.policy?.allowed ? "ALLOWED" : "BLOCKED"}
                </span>
              </div>
              <div className="approval-detail">
                <span className="label">Policy Details</span>
                <span className="text-gray-300 text-right max-w-xs">{approvalData.policy?.reason}</span>
              </div>
            </div>

            <div className="approval-actions mt-4 flex gap-3">
              <button
                className="btn btn-secondary flex-1"
                onClick={() => handleApproval(false)}
                disabled={processingPayment}
              >
                <X size={15} /> Cancel
              </button>
              <button
                className="btn btn-success flex-1"
                onClick={() => handleApproval(true)}
                disabled={processingPayment}
              >
                {processingPayment ? (
                  <span className="spinner w-4 h-4" />
                ) : (
                  <>
                    <Check size={15} /> Confirm Purchase
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
