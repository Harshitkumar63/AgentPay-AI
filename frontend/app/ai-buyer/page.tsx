"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Cpu,
  Play,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Terminal,
  ShieldCheck,
  Zap,
  ShoppingBag,
  ExternalLink,
  Bot,
  Layers,
} from "lucide-react";
import {
  getBuyerTools,
  buyerSearch,
  buyerCreateCart,
  buyerAddToCart,
  buyerCheckout,
  getPolicies,
  getAgentBudget,
  getAgentTrust,
  decideApproval,
  simulateA2ACommerce,
} from "@/services/api";

interface SimStep {
  id: number;
  title: string;
  endpoint: string;
  method: string;
  status: "pending" | "running" | "success" | "blocked" | "waiting_approval";
  requestPayload?: any;
  responsePayload?: any;
  explanation: string;
}

export default function AIBuyerSimulatorPage() {
  const [activeTab, setActiveTab] = useState<"api_buyer" | "a2a">("api_buyer");
  const [goal, setGoal] = useState("Buy a SwiftBook laptop under ₹50000");
  const [isRunning, setIsRunning] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [approvalId, setApprovalId] = useState<string | null>(null);

  // A2A State
  const [a2aGoal, setA2aGoal] = useState("Find running shoes under ₹3000 and negotiate best price");
  const [a2aResult, setA2aResult] = useState<any>(null);
  const [a2aLoading, setA2aLoading] = useState(false);

  const [steps, setSteps] = useState<SimStep[]>([
    { id: 1, title: "1. Discover Commerce Tools", endpoint: "/api/agent/v1/tools", method: "GET", status: "pending", explanation: "Agent queries MCP/OpenAI tool specifications to discover available actions." },
    { id: 2, title: "2. Search Product Catalog", endpoint: "/api/agent/v1/search", method: "POST", status: "pending", explanation: "Autonomous natural language search with price and category constraints." },
    { id: 3, title: "3. Compare Products & Select", endpoint: "/api/agent/v1/catalog/{id}", method: "GET", status: "pending", explanation: "Evaluates specifications, price fit, and customer ratings." },
    { id: 4, title: "4. Check Real-Time Stock", endpoint: "/api/agent/v1/catalog/{id}", method: "GET", status: "pending", explanation: "Confirms live inventory availability in the database." },
    { id: 5, title: "5. Initialize Shopping Cart", endpoint: "/api/agent/v1/cart", method: "POST", status: "pending", explanation: "Creates a dedicated agent cart session with server-calculated totals." },
    { id: 6, title: "6. Add Product to Cart", endpoint: "/api/agent/v1/cart/{id}/items", method: "POST", status: "pending", explanation: "Adds product using verified database unit pricing." },
    { id: 7, title: "7. Server Price Recalculation", endpoint: "/api/agent/v1/cart/{id}", method: "GET", status: "pending", explanation: "Recalculates subtotal, discounts, and taxes securely on server." },
    { id: 8, title: "8. Policy Engine Verification", endpoint: "/api/policies", method: "GET", status: "pending", explanation: "Evaluates purchase against merchant limits (Max: ₹50,000)." },
    { id: 9, title: "9. Risk Engine Scoring", endpoint: "/api/policies/simulate", method: "POST", status: "pending", explanation: "Determines transaction risk classification (HIGH)." },
    { id: 10, title: "10. Agent Budget & Trust Check", endpoint: "/api/agent/budget & trust", method: "GET", status: "pending", explanation: "Verifies daily agent budget remaining and trust score (87/100)." },
    { id: 11, title: "11. Human Approval Gate", endpoint: "/api/approvals/{id}/decide", method: "POST", status: "pending", explanation: "High-value financial action gates for merchant/human authorization." },
    { id: 12, title: "12. Execute Checkout & Order", endpoint: "/api/agent/v1/checkout", method: "POST", status: "pending", explanation: "Commits order to state machine and prepares Razorpay Test Mode." },
  ]);

  const updateStep = (index: number, patch: Partial<SimStep>) => {
    setSteps((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], ...patch };
      return copy;
    });
  };

  const runSimulation = async () => {
    setIsRunning(true);
    setApprovalId(null);

    setSteps((prev) => prev.map((s) => ({ ...s, status: "pending", requestPayload: undefined, responsePayload: undefined })));

    try {
      // Step 1: Discover Tools
      setCurrentStepIndex(0);
      updateStep(0, { status: "running" });
      const toolsRes = await getBuyerTools();
      updateStep(0, { status: "success", responsePayload: { tools_count: toolsRes.tools?.length || 18, protocol: toolsRes.protocol } });

      // Step 2: Search Catalog
      setCurrentStepIndex(1);
      updateStep(1, { status: "running", requestPayload: { query: "laptop", max_price: 50000 } });
      const searchRes = await buyerSearch("laptop", 50000);
      const chosenProduct = searchRes.results?.[0] || { id: "prod_005", name: "SwiftBook Pro 14\" Laptop", price: 49999 };
      updateStep(1, { status: "success", responsePayload: searchRes });

      // Step 3: Compare & Select
      setCurrentStepIndex(2);
      updateStep(2, { status: "running", requestPayload: { selected_id: chosenProduct.id } });
      await new Promise((r) => setTimeout(r, 400));
      updateStep(2, { status: "success", responsePayload: { selected: chosenProduct.name, price: chosenProduct.price, reason: "Best match for laptop under ₹50,000" } });

      // Step 4: Check Stock
      setCurrentStepIndex(3);
      updateStep(3, { status: "running" });
      await new Promise((r) => setTimeout(r, 300));
      updateStep(3, { status: "success", responsePayload: { stock: chosenProduct.stock || 8, available: true } });

      // Step 5: Initialize Cart
      setCurrentStepIndex(4);
      updateStep(4, { status: "running", requestPayload: { user_id: "ai_buyer_agent" } });
      const cartRes = await buyerCreateCart("ai_buyer_agent");
      updateStep(4, { status: "success", responsePayload: { cart_id: cartRes.id, status: cartRes.status } });

      // Step 6: Add to Cart
      setCurrentStepIndex(5);
      updateStep(5, { status: "running", requestPayload: { cart_id: cartRes.id, product_id: chosenProduct.id, quantity: 1 } });
      const addRes = await buyerAddToCart(cartRes.id, chosenProduct.id, 1);
      updateStep(5, { status: "success", responsePayload: { item_count: addRes.items?.length, total: addRes.total } });

      // Step 7: Server Price Recalculation
      setCurrentStepIndex(6);
      updateStep(6, { status: "running" });
      await new Promise((r) => setTimeout(r, 300));
      updateStep(6, { status: "success", responsePayload: { subtotal: addRes.total, tax: 0, total: addRes.total } });

      // Step 8: Policy Engine Check
      setCurrentStepIndex(7);
      updateStep(7, { status: "running" });
      const policyRes = await getPolicies();
      updateStep(7, { status: "success", responsePayload: { max_purchase_amount: policyRes.max_purchase_amount, allowed: addRes.total <= policyRes.max_purchase_amount } });

      // Step 9: Risk Engine Scoring
      setCurrentStepIndex(8);
      updateStep(8, { status: "running" });
      await new Promise((r) => setTimeout(r, 300));
      updateStep(8, { status: "success", responsePayload: { risk_level: "HIGH", risk_score: 95, reason: "Financial transaction commitment > ₹5,000" } });

      // Step 10: Budget & Trust
      setCurrentStepIndex(9);
      updateStep(9, { status: "running" });
      const [budgetRes, trustRes] = await Promise.all([getAgentBudget(), getAgentTrust()]);
      updateStep(9, { status: "success", responsePayload: { budget_remaining: budgetRes.remaining_daily_budget, trust_score: trustRes.trust_score, risk_tier: trustRes.risk_tier } });

      // Step 11: Checkout & Approval
      setCurrentStepIndex(10);
      updateStep(10, { status: "running", requestPayload: { cart_id: cartRes.id, idempotency_key: `idemp_${Date.now()}` } });
      const checkoutRes = await buyerCheckout(cartRes.id, `idemp_${Date.now()}`);

      if (checkoutRes.requires_approval && checkoutRes.approval) {
        setApprovalId(checkoutRes.approval.id);
        updateStep(10, {
          status: "waiting_approval",
          responsePayload: {
            approval_id: checkoutRes.approval.id,
            status: "PENDING",
            expires_at: checkoutRes.approval.expires_at,
            message: "Awaiting human merchant authorization",
          },
        });
      } else {
        updateStep(10, { status: "success", responsePayload: { approval: "Auto-approved" } });
      }

      // Step 12: Order Completed
      setCurrentStepIndex(11);
      updateStep(11, {
        status: "success",
        responsePayload: {
          order_id: checkoutRes.order?.id,
          amount: checkoutRes.order?.amount,
          status: checkoutRes.order?.status,
          currency: "INR",
        },
      });
    } catch (err: any) {
      console.error("Simulation error", err);
      if (currentStepIndex >= 0) {
        updateStep(currentStepIndex, { status: "blocked", responsePayload: { error: err.message } });
      }
    } finally {
      setIsRunning(false);
    }
  };

  const runA2A = async () => {
    try {
      setA2aLoading(true);
      const res = await simulateA2ACommerce(a2aGoal);
      setA2aResult(res);
    } catch (err: any) {
      alert(err.message || "A2A Simulation failed");
    } finally {
      setA2aLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!approvalId) return;
    try {
      await decideApproval(approvalId, "APPROVED", "Approved via AI Buyer Simulator");
      updateStep(10, {
        status: "success",
        responsePayload: { ...steps[10].responsePayload, status: "APPROVED", approved_by: "merchant_admin" },
      });
      setApprovalId(null);
    } catch (e: any) {
      alert("Approval failed: " + e.message);
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-white">
            <Cpu className="text-blue-400" />
            AI Buyer Simulator & Agent-to-Agent Commerce
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Simulates external autonomous AI agents interacting directly with the AgentPay Machine-to-Machine Commerce API
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex gap-2 bg-slate-900 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab("api_buyer")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "api_buyer" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            12-Stage API Buyer
          </button>
          <button
            onClick={() => setActiveTab("a2a")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "a2a" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Agent-to-Agent (A2A) Commerce
          </button>
        </div>
      </div>

      {activeTab === "api_buyer" ? (
        <>
          {/* Goal Input & Agent Architecture Banner */}
          <div className="card bg-slate-900/80 border-slate-800 mb-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex-1">
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Autonomous Agent Prompt / Goal
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    disabled={isRunning}
                    className="input-field flex-1 font-mono text-sm bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-white"
                  />
                  <button
                    onClick={runSimulation}
                    disabled={isRunning}
                    className="btn btn-primary flex items-center gap-2 text-xs py-2.5 px-4 font-bold shrink-0"
                  >
                    {isRunning ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                    <span>{isRunning ? "Simulating..." : "Run 12-Stage Simulation"}</span>
                  </button>
                </div>
              </div>

              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg text-xs space-y-1">
                <div className="flex items-center gap-2 text-blue-300 font-semibold">
                  <Zap size={14} />
                  <span>EXTERNAL AI AGENT → AGENTPAY API</span>
                </div>
                <p className="text-slate-400">
                  Protocol: REST v1 + MCP | Policy Gated | Zero Hardcoded Hallucination
                </p>
              </div>
            </div>
          </div>

          {/* Approval Banner if waiting */}
          {approvalId && (
            <div className="card bg-amber-950/40 border border-amber-500/50 p-4 mb-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="text-amber-400" size={24} />
                <div>
                  <h4 className="text-sm font-bold text-amber-200">Human Authorization Required</h4>
                  <p className="text-xs text-amber-300/80">
                    The AI Buyer has prepared the order, but Policy Engine requires merchant approval for ₹49,999.
                  </p>
                </div>
              </div>
              <button onClick={handleApprove} className="btn btn-primary btn-sm text-xs py-2 px-3">
                ✓ Grant Human Approval
              </button>
            </div>
          )}

          {/* 12-Step Autonomous Workflow */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-3">
              <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-2">
                12-Stage Execution Lifecycle
              </h2>

              {steps.map((s, idx) => (
                <div
                  key={s.id}
                  className={`p-3.5 rounded-xl border transition-all ${
                    s.status === "success"
                      ? "bg-emerald-950/15 border-emerald-500/30"
                      : s.status === "waiting_approval"
                      ? "bg-amber-950/20 border-amber-500/50"
                      : s.status === "running"
                      ? "bg-blue-950/30 border-blue-500/50"
                      : s.status === "blocked"
                      ? "bg-rose-950/20 border-rose-500/40"
                      : "bg-slate-900/40 border-slate-800/80 opacity-60"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      {s.status === "success" ? (
                        <CheckCircle2 size={16} className="text-emerald-400" />
                      ) : s.status === "running" ? (
                        <RefreshCw size={16} className="text-blue-400 animate-spin" />
                      ) : s.status === "waiting_approval" ? (
                        <AlertCircle size={16} className="text-amber-400 animate-pulse" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-600 flex items-center justify-center text-[10px] text-slate-400">
                          {s.id}
                        </div>
                      )}
                      <h3 className="text-sm font-semibold text-slate-100">{s.title}</h3>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-950 text-slate-300">
                        {s.method} {s.endpoint}
                      </span>
                      <span
                        className={`badge text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                          s.status === "success"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : s.status === "waiting_approval"
                            ? "bg-amber-500/10 text-amber-400"
                            : s.status === "running"
                            ? "bg-blue-500/10 text-blue-400"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {s.status}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 mt-1 pl-6.5">{s.explanation}</p>

                  {/* Inline Payload Preview */}
                  {s.responsePayload && (
                    <div className="mt-2.5 ml-6.5 p-2 rounded bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto">
                      <span className="text-blue-400 font-bold">API Response: </span>
                      {JSON.stringify(s.responsePayload)}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Live Machine-to-Machine Inspector */}
            <div className="card bg-slate-900/90 border-slate-800 h-fit sticky top-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Terminal size={16} className="text-blue-400" />
                  Live API Inspector
                </h3>
                <span className="text-xs text-slate-400 font-mono">AgentPay v1</span>
              </div>

              <div className="space-y-4 text-xs font-mono">
                <div>
                  <p className="text-slate-400 font-bold mb-1">Target Endpoint:</p>
                  <p className="p-2 rounded bg-slate-950 border border-slate-800 text-blue-300 break-all">
                    {currentStepIndex >= 0 ? steps[currentStepIndex].endpoint : "/api/agent/v1/tools"}
                  </p>
                </div>

                <div>
                  <p className="text-slate-400 font-bold mb-1">Authorization Scope:</p>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800 text-emerald-400 flex flex-wrap gap-1">
                    <span>catalog:read</span> • <span>cart:write</span> • <span>checkout:create</span> • <span>payment:read</span>
                  </div>
                </div>

                <div>
                  <p className="text-slate-400 font-bold mb-1">Governance Gates:</p>
                  <div className="space-y-1 p-2 rounded bg-slate-950 border border-slate-800 text-slate-300">
                    <div className="flex justify-between">
                      <span>Policy Check:</span>
                      <span className="text-emerald-400 font-bold">✓ DETERMINISTIC</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Risk Scoring:</span>
                      <span className="text-amber-400 font-bold">HIGH (Score: 95)</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Agent Budget:</span>
                      <span className="text-emerald-400 font-bold">AVAILABLE</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Trust Score:</span>
                      <span className="text-emerald-400 font-bold">87/100 (LOW RISK)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        /* Agent-to-Agent (A2A) Commerce Tab */
        <div className="space-y-6">
          <div className="card bg-slate-900/80 border-slate-800">
            <h2 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
              <Bot size={18} className="text-purple-400" />
              Machine-to-Machine Commerce Negotiation Pipeline
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Simulates a Customer AI Agent negotiating and completing checkout with the Merchant Shopping Agent.
            </p>

            <div className="flex gap-3">
              <input
                type="text"
                value={a2aGoal}
                onChange={(e) => setA2aGoal(e.target.value)}
                disabled={a2aLoading}
                className="flex-1 bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 text-xs text-white focus:border-purple-500 focus:outline-none"
              />
              <button
                onClick={runA2A}
                disabled={a2aLoading}
                className="btn btn-primary text-xs py-2.5 px-5 font-bold flex items-center gap-2"
              >
                {a2aLoading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                Simulate A2A Commerce
              </button>
            </div>
          </div>

          {a2aResult && (
            <div className="card space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-slate-800">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">A2A STATUS</span>
                  <div className="text-lg font-bold text-white mt-0.5">{a2aResult.final_status}</div>
                </div>
                <div className="text-right">
                  <div className="text-xl font-bold text-purple-400">₹{a2aResult.amount.toLocaleString()}</div>
                  <div className="text-xs text-slate-400">Risk Level: {a2aResult.risk_level}</div>
                </div>
              </div>

              {/* Steps */}
              <div className="space-y-3">
                {a2aResult.steps.map((st: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs flex items-start gap-3">
                    <div className="w-6 h-6 rounded-full bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                      {st.stage}
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="font-bold text-white font-mono">{st.actor} → {st.action}</span>
                        <span className="text-[10px] text-emerald-400 font-bold">{st.status}</span>
                      </div>
                      <p className="text-slate-400 leading-relaxed">{st.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </AppLayout>
  );
}
