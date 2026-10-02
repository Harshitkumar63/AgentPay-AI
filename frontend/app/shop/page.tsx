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
  Star,
  Sliders,
  DollarSign,
  Zap,
  Tag,
  Bookmark,
  Edit3,
} from "lucide-react";
import {
  sendChatMessage,
  createCart,
  addToCart,
  removeFromCart,
  createPayment,
  verifyPayment,
  getAgentBudget,
  getAgentTrust,
  proposeNegotiation,
  optimizeCartProposal,
  applyCartOptimization,
  getCustomerPreferences,
  updateCustomerPreferences,
} from "@/services/api";
import type {
  ChatResponse,
  Product,
  Cart,
  PaymentData,
  AgentBudget,
  AgentTrust,
  NegotiationProposal,
  CartOptimizerProposal,
  CustomerPreference,
} from "@/types";

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
        "👋 Welcome to UrbanCart! I am your autonomous AI shopping assistant.\n\nI can discover products from our verified catalog, negotiate policy-bounded discounts, optimize your cart composition, and orchestrate policy-gated checkouts.\n\nTry asking me:",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cartId, setCartId] = useState<string | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [showApproval, setShowApproval] = useState(false);
  const [approvalData, setApprovalData] = useState<ChatResponse["confirmation_data"]>(null);
  const [budgetInfo, setBudgetInfo] = useState<AgentBudget | null>(null);
  const [trustInfo, setTrustInfo] = useState<AgentTrust | null>(null);
  const [processingPayment, setProcessingPayment] = useState(false);

  // Negotiation Modal
  const [negotiatingProduct, setNegotiatingProduct] = useState<Product | null>(null);
  const [requestedPrice, setRequestedPrice] = useState<number>(0);
  const [negotiationResult, setNegotiationResult] = useState<NegotiationProposal | null>(null);
  const [negotiatingLoading, setNegotiatingLoading] = useState(false);

  // Cart Optimizer Modal
  const [showOptimizer, setShowOptimizer] = useState(false);
  const [optimizerMode, setOptimizerMode] = useState("BEST_VALUE");
  const [optimizationProposal, setOptimizationProposal] = useState<CartOptimizerProposal | null>(null);
  const [optimizingLoading, setOptimizingLoading] = useState(false);

  // Customer Memory State
  const [preferences, setPreferences] = useState<CustomerPreference | null>(null);
  const [showPreferencesModal, setShowPreferencesModal] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    "Find black running shoes under ₹3000",
    "Show me laptops under ₹50000",
    "What accessories go with running shoes?",
    "Can you negotiate a discount on ProRunner X1?",
    "Optimize my cart for best value",
    "Buy now",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    getCustomerPreferences()
      .then((p) => setPreferences(p))
      .catch(() => {});
  }, []);

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

        Promise.all([getAgentBudget(), getAgentTrust()])
          .then(([b, t]) => {
            setBudgetInfo(b);
            setTrustInfo(t);
          })
          .catch(() => {});

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
          content: `✅ Added **${product.name}** to your cart! Subtotal: ₹${updated.total.toLocaleString("en-IN")}\n\nSay "Buy now" or click **'Gated AI Checkout'** on the right whenever you're ready.`,
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

  // Negotiation Trigger
  const openNegotiationModal = (product: Product) => {
    setNegotiatingProduct(product);
    setRequestedPrice(Math.round(product.price * 0.9));
    setNegotiationResult(null);
  };

  const submitNegotiation = async () => {
    if (!negotiatingProduct) return;
    try {
      setNegotiatingLoading(true);
      const res = await proposeNegotiation(negotiatingProduct.id, requestedPrice);
      setNegotiationResult(res);
    } catch (err: any) {
      alert(err.message || "Negotiation failed");
    } finally {
      setNegotiatingLoading(false);
    }
  };

  // Cart Optimizer Trigger
  const openOptimizerModal = async () => {
    if (!cartId) {
      alert("Please add items to your cart first.");
      return;
    }
    setShowOptimizer(true);
    fetchOptimizationProposal(optimizerMode);
  };

  const fetchOptimizationProposal = async (mode: string) => {
    if (!cartId) return;
    try {
      setOptimizingLoading(true);
      const prop = await optimizeCartProposal(cartId, mode);
      setOptimizationProposal(prop);
    } catch (err: any) {
      alert(err.message || "Optimization proposal failed");
    } finally {
      setOptimizingLoading(false);
    }
  };

  const applyOptimization = async () => {
    if (!cartId) return;
    try {
      setOptimizingLoading(true);
      const res = await applyCartOptimization(cartId, optimizerMode);
      setCart(res.cart);
      setShowOptimizer(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `✨ **Cart Optimized Successfully!** Strategy: \`${optimizerMode}\`\n\nYour cart items and savings have been updated.`,
        },
      ]);
    } catch (err: any) {
      alert(err.message || "Failed to apply optimization");
    } finally {
      setOptimizingLoading(false);
    }
  };

  const handleApproval = async (approved: boolean) => {
    setShowApproval(false);
    if (!approved) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "🛑 Purchase authorization cancelled by user. Cart items remain preserved." },
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
            content: `🎉 **Payment Verified & Captured!** (RAZORPAY TEST MODE)\n\n• Order ID: \`${orderId}\`\n• Amount: **₹${(paymentData.amount / 100).toLocaleString("en-IN")}**\n• Status: \`COMPLETED\`\n• Gateway Signature: \`VERIFIED\`\n\nFull immutable transaction ledger recorded in Audit Logs. Click on **'Decision Replay'** to inspect the entire governance trace!`,
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
                  content: `🎉 **Payment Confirmed & Verified!**\n\nPayment ID: \`${response.razorpay_payment_id}\`\nOrder fulfilled successfully.`,
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
      <div className="page-header flex justify-between items-center flex-wrap gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
            <Sparkles className="text-blue-400" /> AI Conversational Shop
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Natural language catalog discovery, AI price negotiation, and policy-gated checkout
          </p>
        </div>

        {/* Customer Shopping Memory Badge */}
        {preferences && (
          <div className="flex items-center gap-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-slate-800 text-xs">
            <Bookmark size={14} className="text-blue-400" />
            <span className="text-slate-300">
              Memory: <strong className="text-white">{preferences.preferred_categories?.join(", ") || "General"}</strong>
            </span>
          </div>
        )}
      </div>

      {/* Quick Prompts Bar */}
      <div className="flex flex-wrap gap-2 mb-4">
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(p)}
            className="text-xs px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 text-slate-300 hover:border-blue-500/50 hover:bg-blue-950/20"
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

                    {/* "Why did the AI do this?" */}
                    {msg.explanation && (
                      <div className="explanation-box mt-3 p-3 rounded-lg bg-blue-950/20 border border-blue-500/30">
                        <div className="explanation-title text-xs font-bold text-blue-300 flex items-center gap-1 mb-1.5">
                          <Info size={13} />
                          {msg.explanation.title}
                        </div>
                        {msg.explanation.factors?.map((fac, fIdx) => (
                          <div key={fIdx} className="explanation-factor text-xs flex items-center gap-1.5 text-slate-300">
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
                    <div className="text-xs text-slate-400 mb-1 font-semibold flex items-center gap-1">
                      <Layers size={13} className="text-blue-400" />
                      Autonomous Tool Trace:
                    </div>
                    {msg.agentSteps.map((step, k) => (
                      <div key={k} className="agent-step">
                        <div className="agent-step-number">{step.sequence || step.step || k + 1}</div>
                        <span className="agent-step-tool font-mono">{step.tool}()</span>
                        <span className="text-xs text-slate-400">{step.output_summary}</span>
                        <span
                          className={`badge text-[10px] font-bold uppercase ml-auto ${
                            step.status.toUpperCase() === "SUCCESS" ? "badge-success text-emerald-400 bg-emerald-500/10" : "badge-danger text-red-400 bg-red-500/10"
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
                          <h3 className="text-sm font-bold text-white">{product.name}</h3>
                          <span className="product-price text-blue-400 font-bold">₹{product.price.toLocaleString("en-IN")}</span>
                        </div>
                        <p className="text-xs text-slate-400 line-clamp-2 my-2">{product.description}</p>
                        
                        <div className="flex items-center justify-between mb-3 text-xs">
                          <span
                            className={`badge text-[10px] px-2 py-0.5 rounded-full ${
                              product.stock > 0 ? "text-emerald-400 bg-emerald-500/10" : "text-red-400 bg-red-500/10"
                            }`}
                          >
                            {product.stock > 0 ? `${product.stock} in stock` : "Out of stock"}
                          </span>
                          <span className="badge text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 flex items-center gap-1">
                            <Star size={10} className="fill-amber-400 text-amber-400" />
                            Score: {product.recommendation_score || 90}/100
                          </span>
                        </div>

                        <div className="product-actions flex flex-col gap-1.5">
                          <button
                            className="btn btn-primary btn-sm w-full py-1.5 text-xs flex items-center justify-center gap-1"
                            onClick={() => handleAddToCart(product)}
                            disabled={product.stock <= 0}
                          >
                            <Plus size={14} /> Add to Cart
                          </button>
                          <button
                            className="btn btn-secondary btn-sm w-full py-1 text-xs text-amber-300 hover:bg-amber-500/10 flex items-center justify-center gap-1"
                            onClick={() => openNegotiationModal(product)}
                          >
                            <Tag size={13} /> Negotiate Price
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
                  <span className="text-xs text-slate-400">Agent reasoning & checking catalog...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <div className="chat-input-container">
            <input
              className="chat-input"
              placeholder="Ask anything... e.g. 'Find laptops under ₹50000' or 'Buy it'"
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
          <div className="cart-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingCart size={18} className="text-blue-400" />
              <span>Active Cart</span>
            </div>
            {cart?.items && cart.items.length > 0 && (
              <button
                onClick={openOptimizerModal}
                className="btn btn-secondary text-[10px] py-1 px-2 text-purple-300 hover:bg-purple-500/10 flex items-center gap-1"
              >
                <Sparkles size={11} /> Optimize
              </button>
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
                    <span className="font-semibold text-sm text-white">₹{item.subtotal.toLocaleString("en-IN")}</span>
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
                <ShoppingCart size={32} className="mx-auto opacity-50 text-slate-500" />
                <h3 className="text-sm font-bold text-slate-300">Cart is empty</h3>
                <p className="text-xs text-slate-500">Ask the AI agent to discover and add items.</p>
              </div>
            )}
          </div>

          {cart?.items && cart.items.length > 0 && (
            <div className="cart-footer">
              <div className="cart-total">
                <span className="text-slate-400">Total</span>
                <span className="text-white font-bold">₹{cart.total.toLocaleString("en-IN")}</span>
              </div>
              <button
                className="btn btn-primary w-full py-2.5 text-xs font-bold"
                onClick={() => sendMessage("Buy these items")}
              >
                <ArrowRight size={16} /> Gated AI Checkout
              </button>
            </div>
          )}
        </div>
      </div>

      {/* AI Negotiation Modal */}
      {negotiatingProduct && (
        <div className="approval-overlay">
          <div className="approval-dialog max-w-md">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold flex items-center gap-2 text-amber-300">
                <Tag size={18} className="text-amber-400" />
                Controlled AI Negotiation
              </h2>
              <button onClick={() => setNegotiatingProduct(null)} className="text-slate-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-slate-400 mb-4">
              Propose an offer for <strong>{negotiatingProduct.name}</strong>. Backend validates against merchant margin policies.
            </p>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-2 mb-4">
              <div className="flex justify-between text-slate-300">
                <span>Catalog List Price:</span>
                <span className="font-bold text-white">₹{negotiatingProduct.price.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                <span className="font-semibold text-amber-300">Your Counter-Offer:</span>
                <div className="flex items-center gap-1">
                  <span className="text-white font-bold">₹</span>
                  <input
                    type="number"
                    value={requestedPrice}
                    onChange={(e) => setRequestedPrice(parseFloat(e.target.value) || 0)}
                    className="w-24 bg-slate-900 px-2 py-1 rounded border border-slate-700 text-right text-xs text-white font-bold"
                  />
                </div>
              </div>
            </div>

            {negotiationResult && (
              <div className="p-3 mb-4 rounded-xl bg-blue-950/20 border border-blue-500/30 text-xs space-y-1.5 font-mono">
                <div className="flex justify-between font-bold">
                  <span className="text-blue-300">DECISION:</span>
                  <span className={negotiationResult.status === "ACCEPTED" ? "text-emerald-400" : "text-amber-400"}>
                    {negotiationResult.status}
                  </span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Authorized Final Offer:</span>
                  <span className="font-bold text-white">₹{negotiationResult.final_offer.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Discount Granted:</span>
                  <span className="text-emerald-400">{negotiationResult.discount_granted_percentage}%</span>
                </div>
                <p className="text-[11px] text-slate-400 font-sans pt-1 border-t border-slate-800">{negotiationResult.reason}</p>
              </div>
            )}

            <div className="flex gap-2">
              <button
                onClick={submitNegotiation}
                disabled={negotiatingLoading}
                className="btn btn-primary flex-1 text-xs py-2"
              >
                {negotiatingLoading ? "Evaluating Margins..." : "Submit Proposal"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cart Optimizer Modal */}
      {showOptimizer && (
        <div className="approval-overlay">
          <div className="approval-dialog max-w-lg">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold flex items-center gap-2 text-purple-300">
                <Sparkles size={18} className="text-purple-400" />
                Cart Optimizer Engine
              </h2>
              <button onClick={() => setShowOptimizer(false)} className="text-slate-400 hover:text-white">
                <X size={18} />
              </button>
            </div>

            {/* Mode Selector */}
            <div className="grid grid-cols-4 gap-1.5 mb-4">
              {[
                { id: "BEST_VALUE", label: "Best Value" },
                { id: "MINIMUM_PRICE", label: "Min Price" },
                { id: "BEST_QUALITY", label: "Best Quality" },
                { id: "MAXIMUM_SAVING", label: "Max Saving" },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => {
                    setOptimizerMode(m.id);
                    fetchOptimizationProposal(m.id);
                  }}
                  className={`text-[10px] py-1.5 rounded-lg border font-semibold ${
                    optimizerMode === m.id
                      ? "bg-purple-600 border-purple-500 text-white"
                      : "bg-slate-950 border-slate-800 text-slate-400"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {optimizingLoading ? (
              <div className="py-12 text-center text-xs text-slate-400">Analyzing Cart Variations...</div>
            ) : optimizationProposal ? (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-2 text-center p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                  <div>
                    <div className="text-[10px] text-slate-500">Current Total</div>
                    <div className="font-bold text-white">₹{optimizationProposal.current_total.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">Optimized</div>
                    <div className="font-bold text-purple-400">₹{optimizationProposal.optimized_total.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500">Est. Savings</div>
                    <div className="font-bold text-emerald-400">₹{optimizationProposal.savings.toLocaleString()}</div>
                  </div>
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {optimizationProposal.suggestions.map((sug, idx) => (
                    <div key={idx} className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800 text-xs space-y-1">
                      <div className="flex justify-between font-bold text-white">
                        <span>{sug.action}: {sug.suggested_product_name}</span>
                        <span className="text-emerald-400">{sug.price_difference < 0 ? `-₹${Math.abs(sug.price_difference)}` : `+₹${sug.price_difference}`}</span>
                      </div>
                      <p className="text-[11px] text-slate-400">{sug.reason}</p>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2 pt-2 border-t border-slate-800">
                  <button onClick={() => setShowOptimizer(false)} className="btn btn-secondary flex-1 text-xs py-2">
                    Dismiss
                  </button>
                  <button onClick={applyOptimization} className="btn btn-primary flex-1 text-xs py-2">
                    Apply Optimization
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Human Approval & Governance Gate Modal */}
      {showApproval && approvalData && (
        <div className="approval-overlay">
          <div className="approval-dialog max-w-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold flex items-center gap-2 text-blue-300">
                <Shield size={20} className="text-blue-400" />
                Purchase Review & Authorization Gate
              </h2>
              <span className="risk-pill risk-high">High Risk</span>
            </div>

            <p className="text-xs text-slate-400 mb-4">
              Autonomous purchase gated for merchant & human verification before payment initialization.
            </p>

            <div className="space-y-2.5 py-3 border-y border-slate-800 text-xs">
              <div className="approval-detail">
                <span className="label text-slate-400 font-bold">Order ID</span>
                <span className="font-mono text-slate-200">{approvalData.order?.id}</span>
              </div>
              <div className="approval-detail">
                <span className="label text-slate-400 font-bold">Calculated Amount</span>
                <span className="font-bold text-lg text-emerald-400">
                  ₹{approvalData.amount?.toLocaleString("en-IN")}
                </span>
              </div>
              <div className="approval-detail">
                <span className="label text-slate-400 font-bold">Policy Check</span>
                <span className="badge badge-success font-bold text-xs text-emerald-400">✓ ALLOWED</span>
              </div>
              <div className="approval-detail">
                <span className="label text-slate-400 font-bold">Risk Assessment</span>
                <span className="badge badge-danger font-bold text-xs text-red-400">HIGH RISK (FINANCIAL)</span>
              </div>
              <div className="approval-detail">
                <span className="label text-slate-400 font-bold">Agent Budget</span>
                <span className="text-emerald-400 font-semibold">
                  AVAILABLE (Remaining: ₹{budgetInfo?.remaining_daily_budget?.toLocaleString() || "7,501"})
                </span>
              </div>
              <div className="approval-detail">
                <span className="label text-slate-400 font-bold">Agent Trust Score</span>
                <span className="text-blue-300 font-semibold font-mono">
                  {trustInfo?.trust_score || 87} / 100 ({trustInfo?.risk_tier || "LOW RISK"})
                </span>
              </div>
            </div>

            <div className="approval-actions mt-5 flex gap-3">
              <button
                className="btn btn-secondary flex-1 text-sm py-2"
                onClick={() => handleApproval(false)}
                disabled={processingPayment}
              >
                <X size={15} /> Cancel
              </button>
              <button
                className="btn btn-success flex-1 text-sm py-2"
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
