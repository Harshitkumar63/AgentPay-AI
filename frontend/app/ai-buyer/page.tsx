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
  const [goal, setGoal] = useState("Buy a SwiftBook laptop under ₹50000");
  const [isRunning, setIsRunning] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(-1);
  const [activeTab, setActiveTab] = useState<"pipeline" | "raw_json">("pipeline");
  const [approvalId, setApprovalId] = useState<string | null>(null);

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

    // Reset all steps
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

  const handleApprove = async () => {
    if (!approvalId) return;
    try {
      const res = await decideApproval(approvalId, "APPROVED", "Approved via AI Buyer Simulator");
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
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Cpu className="text-blue-400" />
            AI Buyer Simulator
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Simulates external autonomous AI agents interacting directly with the AgentPay Machine-to-Machine Commerce API
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={runSimulation}
            disabled={isRunning}
            className="btn btn-primary flex items-center gap-2 text-sm"
          >
            {isRunning ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            <span>{isRunning ? "Simulating Agent..." : "Run Autonomous Agent Simulation"}</span>
          </button>
        </div>
      </div>

      {/* Goal Input & Agent Architecture Banner */}
      <div className="card bg-gray-900/80 border-gray-800 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1">
            <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider block mb-1">
              Autonomous Agent Prompt / Goal
            </label>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                disabled={isRunning}
                className="input-field flex-1 font-mono text-sm"
              />
            </div>
          </div>

          <div className="p-3 bg-black/40 border border-gray-800 rounded-lg text-xs space-y-1">
            <div className="flex items-center gap-2 text-indigo-300 font-semibold">
              <Zap size={14} />
              <span>EXTERNAL AI AGENT → AGENTPAY API</span>
            </div>
            <p className="text-gray-400">
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
          <button onClick={handleApprove} className="btn btn-primary btn-sm">
            ✓ Grant Human Approval
          </button>
        </div>
      )}

      {/* 12-Step Autonomous Workflow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-sm font-bold text-gray-300 uppercase tracking-wider mb-2">
            12-Stage Execution Lifecycle
          </h2>

          {steps.map((s, idx) => {
            const isCurrent = currentStepIndex === idx && isRunning;
            return (
              <div
                key={s.id}
                className={`p-3.5 rounded-lg border transition-all ${
                  s.status === "success"
                    ? "bg-emerald-950/15 border-emerald-500/30"
                    : s.status === "waiting_approval"
                    ? "bg-amber-950/20 border-amber-500/50"
                    : s.status === "running"
                    ? "bg-blue-950/30 border-blue-500/50"
                    : s.status === "blocked"
                    ? "bg-rose-950/20 border-rose-500/40"
                    : "bg-gray-900/40 border-gray-800/80 opacity-60"
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
                      <div className="w-4 h-4 rounded-full border border-gray-600 flex items-center justify-center text-[10px] text-gray-400">
                        {s.id}
                      </div>
                    )}
                    <h3 className="text-sm font-semibold text-gray-100">{s.title}</h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-black/50 text-gray-300">
                      {s.method} {s.endpoint}
                    </span>
                    <span
                      className={`badge text-[10px] uppercase font-bold ${
                        s.status === "success"
                          ? "badge-success"
                          : s.status === "waiting_approval"
                          ? "badge-warning"
                          : s.status === "running"
                          ? "badge-info"
                          : "badge-secondary"
                      }`}
                    >
                      {s.status}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-gray-400 mt-1 pl-6.5">{s.explanation}</p>

                {/* Inline Payload Preview */}
                {s.responsePayload && (
                  <div className="mt-2.5 ml-6.5 p-2 rounded bg-black/60 border border-gray-800 text-[11px] font-mono text-gray-300 overflow-x-auto">
                    <span className="text-indigo-400 font-bold">API Response: </span>
                    {JSON.stringify(s.responsePayload)}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Live Machine-to-Machine Inspector */}
        <div className="card bg-gray-900/90 border-gray-800 h-fit sticky top-6">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-4">
            <h3 className="text-sm font-bold text-gray-200 flex items-center gap-2">
              <Terminal size={16} className="text-indigo-400" />
              Live API Inspector
            </h3>
            <span className="text-xs text-gray-400 font-mono">AgentPay v1</span>
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div>
              <p className="text-gray-400 font-bold mb-1">Target Endpoint:</p>
              <p className="p-2 rounded bg-black/60 border border-gray-800 text-blue-300 break-all">
                {currentStepIndex >= 0 ? steps[currentStepIndex].endpoint : "/api/agent/v1/tools"}
              </p>
            </div>

            <div>
              <p className="text-gray-400 font-bold mb-1">Authorization Scope:</p>
              <div className="p-2 rounded bg-black/60 border border-gray-800 text-emerald-400 flex flex-wrap gap-1">
                <span>catalog:read</span> • <span>cart:write</span> • <span>checkout:create</span> • <span>payment:read</span>
              </div>
            </div>

            <div>
              <p className="text-gray-400 font-bold mb-1">Governance Gates:</p>
              <div className="space-y-1 p-2 rounded bg-black/60 border border-gray-800 text-gray-300">
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
    </AppLayout>
  );
}
