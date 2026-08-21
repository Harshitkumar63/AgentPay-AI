"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Settings as SettingsIcon, Shield, Save, Check } from "lucide-react";
import { getPolicies, updatePolicies } from "@/services/api";
import type { Policy } from "@/types";

export default function SettingsPage() {
  const [policy, setPolicy] = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Form state
  const [maxAmount, setMaxAmount] = useState(50000);
  const [maxDiscount, setMaxDiscount] = useState(20);
  const [approvalRequired, setApprovalRequired] = useState(true);

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

  return (
    <AppLayout>
      <div className="page-header">
        <h1><SettingsIcon size={28} style={{ display: "inline", marginRight: 10, verticalAlign: "middle" }} />Settings</h1>
        <p>Configure merchant policies and agent behavior</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : (
        <div style={{ maxWidth: 640 }}>
          {/* Policy Engine Settings */}
          <div className="card" style={{ marginBottom: 24 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20, display: "flex", alignItems: "center", gap: 8 }}>
              <Shield size={20} style={{ color: "#6c5ce7" }} /> Policy Engine
            </h2>

            <div className="form-group">
              <label className="form-label">Maximum Purchase Amount (₹)</label>
              <input
                className="form-input"
                type="number"
                value={maxAmount}
                onChange={(e) => setMaxAmount(Number(e.target.value))}
              />
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                AI agent will be blocked from creating orders above this amount.
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
            </div>

            <div className="form-group">
              <label className="form-label" style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={approvalRequired}
                  onChange={(e) => setApprovalRequired(e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: "#6c5ce7" }}
                />
                Require User Approval for Purchases
              </label>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                When enabled, the AI agent must get explicit user confirmation before processing payments.
              </p>
            </div>

            <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
              {saved ? <Check size={16} /> : <Save size={16} />}
              {saving ? "Saving..." : saved ? "Saved!" : "Save Policy"}
            </button>
          </div>

          {/* Environment Info */}
          <div className="card">
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>Environment</h2>
            <div style={{ display: "grid", gap: 12 }}>
              <div className="approval-detail">
                <span className="label">Mode</span>
                <span className="badge badge-warning">DEMO MODE</span>
              </div>
              <div className="approval-detail">
                <span className="label">Merchant</span>
                <span>UrbanCart (merchant_001)</span>
              </div>
              <div className="approval-detail">
                <span className="label">Policy ID</span>
                <span>{policy?.id || "—"}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
