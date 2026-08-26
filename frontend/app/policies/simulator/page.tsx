"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Sliders,
  Play,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  Zap,
} from "lucide-react";
import { simulatePolicy, getPolicies } from "@/services/api";
import { PolicySimulation } from "@/types";

export default function PolicySimulatorPage() {
  const [amount, setAmount] = useState<number>(7500);
  const [discount, setDiscount] = useState<number>(10);
  const [action, setAction] = useState<string>("create_order");
  const [agentId, setAgentId] = useState<string>("default_agent");
  const [simulation, setSimulation] = useState<PolicySimulation | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await simulatePolicy({
        amount,
        discount_percentage: discount,
        action,
        agent_id: agentId,
      });
      setSimulation(res);
    } catch (e: any) {
      alert("Simulation failed: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sliders className="text-indigo-400" />
          Policy & Governance Simulator
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Evaluate hypothetical financial transactions, discount requests, and tool calls against live merchant policies, risk scoring, and agent budgets without modifying live data.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Simulation Controls */}
        <div className="card bg-gray-900/80 border-gray-800 space-y-4">
          <h2 className="text-base font-bold text-gray-100 flex items-center gap-2 border-b border-gray-800 pb-3">
            <Zap size={16} className="text-amber-400" />
            Simulation Parameters
          </h2>

          <div>
            <label className="text-xs font-semibold text-gray-400 block mb-1">
              Purchase Amount (INR)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
              className="input-field w-full font-mono text-sm"
              placeholder="e.g., 7500"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-400 block mb-1">
              Discount Percentage (%)
            </label>
            <input
              type="number"
              value={discount}
              onChange={(e) => setDiscount(parseFloat(e.target.value) || 0)}
              className="input-field w-full font-mono text-sm"
              placeholder="e.g., 10"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-400 block mb-1">
              Commercial Action
            </label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="input-field w-full text-sm"
            >
              <option value="create_order">create_order (Financial Charge)</option>
              <option value="add_to_cart">add_to_cart (Cart Mutation)</option>
              <option value="search_products">search_products (Read-Only)</option>
              <option value="launch_campaign">launch_campaign (Budget Disbursement)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-400 block mb-1">
              Agent Identity
            </label>
            <input
              type="text"
              value={agentId}
              onChange={(e) => setAgentId(e.target.value)}
              className="input-field w-full font-mono text-sm"
            />
          </div>

          <button
            onClick={handleSimulate}
            disabled={loading}
            className="btn btn-primary w-full flex items-center justify-center gap-2 mt-4"
          >
            {loading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            <span>Run Policy Simulation</span>
          </button>
        </div>

        {/* Evaluation Output */}
        <div className="lg:col-span-2 space-y-6">
          {simulation ? (
            <div className="card bg-gray-900/80 border-gray-800 space-y-6 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                <div className="flex items-center gap-3">
                  {simulation.decision.allowed ? (
                    <ShieldCheck className="text-emerald-400" size={28} />
                  ) : (
                    <ShieldAlert className="text-rose-400" size={28} />
                  )}
                  <div>
                    <h3 className="text-base font-bold text-gray-100">
                      Outcome: {simulation.decision.allowed ? "ALLOWED" : "BLOCKED"}
                    </h3>
                    <p className="text-xs text-gray-400">{simulation.decision.reason}</p>
                  </div>
                </div>

                <span
                  className={`badge uppercase font-bold text-xs ${
                    simulation.decision.allowed ? "badge-success" : "badge-danger"
                  }`}
                >
                  {simulation.decision.allowed ? "✓ Policy Passed" : "✗ Policy Blocked"}
                </span>
              </div>

              {/* Risk & Governance Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-3 rounded-lg bg-black/40 border border-gray-800 space-y-1">
                  <span className="text-[11px] font-bold text-gray-400 uppercase">Risk Classification</span>
                  <p className="text-sm font-bold text-amber-300">
                    {simulation.decision.risk_level} ({simulation.decision.risk_score}/100)
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-black/40 border border-gray-800 space-y-1">
                  <span className="text-[11px] font-bold text-gray-400 uppercase">Human Approval</span>
                  <p className="text-sm font-bold text-indigo-300">
                    {simulation.decision.requires_approval ? "MANDATED" : "NOT REQUIRED"}
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-black/40 border border-gray-800 space-y-1">
                  <span className="text-[11px] font-bold text-gray-400 uppercase">Agent Trust Tier</span>
                  <p className="text-sm font-bold text-emerald-400">
                    {simulation.decision.details?.trust?.risk_tier || "LOW RISK"}
                  </p>
                </div>
              </div>

              {/* Breakdown Details */}
              <div className="space-y-3 font-mono text-xs p-4 rounded-lg bg-black/60 border border-gray-800">
                <h4 className="text-gray-400 font-bold uppercase tracking-wider">Evaluation Breakdown</h4>
                <div className="space-y-1.5 text-gray-300">
                  <p>• Policy Cap: ₹{simulation.decision.details?.maximum_allowed?.toLocaleString() || "50,000"}</p>
                  <p>• Requested Amount: ₹{amount.toLocaleString()}</p>
                  <p>• Discount Check: {discount}% (Cap: {simulation.decision.details?.max_discount_percentage || 20}%)</p>
                  <p>• Agent Daily Budget: ₹{simulation.decision.details?.budget?.daily_limit?.toLocaleString() || "10,000"}</p>
                  <p>• Remaining Agent Budget: ₹{simulation.decision.details?.budget?.remaining_budget?.toLocaleString() || "7,501"}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="card text-center p-12 bg-gray-900/40 border-dashed border-gray-800">
              <Sliders className="mx-auto text-gray-500 mb-3" size={32} />
              <h3 className="text-sm font-bold text-gray-300">Ready to Simulate</h3>
              <p className="text-xs text-gray-500 mt-1">
                Adjust parameters on the left and click &apos;Run Policy Simulation&apos; to view real-time governance output.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
