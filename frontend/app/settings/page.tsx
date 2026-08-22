"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Settings as SettingsIcon,
  Shield,
  Save,
  Check,
  Play,
  Sliders,
  AlertTriangle,
  ShieldCheck,
  CheckCircle,
  XCircle,
} from "lucide-react";
import { getPolicies, updatePolicies, simulatePolicy } from "@/services/api";
import type { Policy, PolicySimulation } from "@/types";

export default function SettingsPage() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Form state
  const [maxAmount, setMaxAmount] = useState(50000);
  const [maxDiscount, setMaxDiscount] = useState(20);
  const [approvalRequired, setApprovalRequired] = useState(true);

  // Policy Simulator State (Phase 28)
  const [simAmount, setSimAmount] = useState(7500);
  const [simDiscount, setSimDiscount] = useState(10);
  const [simAction, setSimAction] = useState("create_order");
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<PolicySimulation | null>(null);

  useEffect(() => {
    getPolicies()
      .then((p) => {
        setPolicy(p);
        setMaxAmount(p.max_purchase_amount);
        setMaxDiscount(p.max_discount_percentage);
        setApprovalRequired(p.approval_required);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updatePolicies("merchant_001", {
        max_purchase_amount: maxAmount,
        max_discount_percentage: maxDiscount,
        approval_required: approvalRequired,
      });
      setPolicy(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error("Save error:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    try {
      const res = await simulatePolicy({
        amount: simAmount,
        discount_percentage: simDiscount,
        action: simAction,
      });
      setSimResult(res);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sliders className="text-indigo-400" />
          Policy Engine & Simulator
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Define financial governance boundaries and simulate automated compliance rules in real-time
        </p>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Policy Engine Configuration */}
          <div className="card">
            <h2 className="text-lg font-bold mb-5 flex items-center gap-2 text-indigo-300">
              <Shield size={20} className="text-indigo-400" /> Financial Policy Settings
            </h2>

            <div className="form-group">
              <label className="form-label">Maximum Transaction Amount (₹)</label>
              <input
                className="form-input"
                type="number"
                value={maxAmount}
                onChange={(e) => setMaxAmount(Number(e.target.value))}
              />
              <p className="text-xs text-gray-400 mt-1">
                AI agents and automated tools cannot execute transactions exceeding this limit without policy blockage.
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Maximum Discount Percentage (%)</label>
              <input
                className="form-input"
                type="number"
                value={maxDiscount}
                onChange={(e) => setMaxDiscount(Number(e.target.value))}
              />
              <p className="text-xs text-gray-400 mt-1">
                Limits coupon codes, campaign offers, and dynamic AI discount concessions.
              </p>
            </div>

            <div className="form-group">
              <label className="form-label flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={approvalRequired}
                  onChange={(e) => setApprovalRequired(e.target.checked)}
                  className="w-4 h-4 accent-indigo-600 rounded"
                />
                <span className="font-semibold text-gray-200">Enforce Human Approval Gate</span>
              </label>
              <p className="text-xs text-gray-400 mt-1">
                When enabled, financial commitments require interactive human confirmation before payment dispatch.
              </p>
            </div>

            <div className="mt-6 flex justify-end">
              <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saved ? <Check size={16} /> : <Save size={16} />}
                {saving ? "Saving..." : saved ? "Policy Saved!" : "Update Policy"}
              </button>
            </div>
          </div>

          {/* Interactive Policy Simulator (Phase 28) */}
          <div className="card bg-gradient-to-br from-gray-900 to-indigo-950/30 border-indigo-500/30">
            <h2 className="text-lg font-bold mb-2 flex items-center gap-2 text-indigo-300">
              <Play size={18} className="text-emerald-400" /> Interactive Policy Simulator
            </h2>
            <p className="text-xs text-gray-400 mb-4">
              Test synthetic transactions to demonstrate automated risk scoring and policy decisions without modifying state.
            </p>

            <form onSubmit={handleSimulate} className="space-y-4">
              <div className="form-group mb-2">
                <label className="form-label">Simulated Purchase Amount (₹)</label>
                <input
                  className="form-input"
                  type="number"
                  value={simAmount}
                  onChange={(e) => setSimAmount(Number(e.target.value))}
                />
              </div>

              <div className="form-group mb-2">
                <label className="form-label">Simulated Discount (%)</label>
                <input
                  className="form-input"
                  type="number"
                  value={simDiscount}
                  onChange={(e) => setSimDiscount(Number(e.target.value))}
                />
              </div>

              <div className="form-group mb-4">
                <label className="form-label">Target Action</label>
                <select
                  value={simAction}
                  onChange={(e) => setSimAction(e.target.value)}
                  className="form-input bg-gray-900 text-gray-200"
                >
                  <option value="create_order">create_order (High Risk)</option>
                  <option value="add_to_cart">add_to_cart (Medium Risk)</option>
                  <option value="search_products">search_products (Low Risk)</option>
                </select>
              </div>

              <button type="submit" disabled={simulating} className="btn btn-secondary w-full">
                {simulating ? <span className="spinner w-4 h-4" /> : "Run Policy Evaluation"}
              </button>
            </form>

            {/* Simulation Result */}
            {simResult && (
              <div className="mt-5 p-4 rounded-lg bg-black/60 border border-indigo-500/40 text-xs space-y-2">
                <div className="flex items-center justify-between border-b border-gray-800 pb-2">
                  <span className="font-bold text-gray-300">SIMULATION DECISION:</span>
                  <span
                    className={`badge font-bold ${
                      simResult.decision.allowed ? "badge-success" : "badge-danger"
                    }`}
                  >
                    {simResult.decision.allowed ? "✓ ALLOWED" : "✗ BLOCKED"}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-400">Risk Assessment:</span>
                  <span
                    className={`risk-pill ${
                      simResult.decision.risk_level === "LOW"
                        ? "risk-low"
                        : simResult.decision.risk_level === "MEDIUM"
                        ? "risk-medium"
                        : "risk-high"
                    }`}
                  >
                    {simResult.decision.risk_level} ({simResult.decision.risk_score}/100)
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-400">Requires Approval:</span>
                  <span className="text-gray-200 font-semibold">
                    {simResult.decision.requires_approval ? "YES (Human Gate)" : "NO (Auto-Approved)"}
                  </span>
                </div>

                <div className="pt-1">
                  <span className="text-gray-400">Reason:</span>
                  <p className="text-gray-200 font-mono mt-0.5">{simResult.decision.reason}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  );
}
