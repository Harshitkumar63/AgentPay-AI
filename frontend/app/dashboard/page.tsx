"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  DollarSign, ShoppingCart, TrendingUp, Target,
  Bot, ArrowUpRight, Zap, Package
} from "lucide-react";
import { getRevenueAnalytics, getGrowthRecommendations, getAgentActions } from "@/services/api";
import type { RevenueAnalytics, GrowthRecommendation, AgentAction } from "@/types";

export default function Dashboard() {
  const [revenue, setRevenue] = useState<RevenueAnalytics | null>(null);
  const [growth, setGrowth] = useState<GrowthRecommendation[]>([]);
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [rev, gr, act] = await Promise.all([
          getRevenueAnalytics().catch(() => null),
          getGrowthRecommendations().catch(() => []),
          getAgentActions(undefined, 10).catch(() => []),
        ]);
        setRevenue(rev);
        setGrowth(gr);
        setActions(act);
      } catch (e) {
        console.error("Dashboard load error:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stats = [
    {
      label: "Revenue",
      value: `₹${(revenue?.total_revenue ?? 0).toLocaleString("en-IN")}`,
      sub: revenue?.period ?? "all time",
      icon: DollarSign,
      color: "#00b894",
      bg: "rgba(0,184,148,0.1)",
    },
    {
      label: "Orders",
      value: revenue?.total_orders ?? 0,
      sub: `${revenue?.successful_orders ?? 0} completed`,
      icon: ShoppingCart,
      color: "#74b9ff",
      bg: "rgba(116,185,255,0.1)",
    },
    {
      label: "Conversion Rate",
      value: `${revenue?.conversion_rate ?? 0}%`,
      sub: "Order success rate",
      icon: TrendingUp,
      color: "#fdcb6e",
      bg: "rgba(253,203,110,0.1)",
    },
    {
      label: "Avg Order Value",
      value: `₹${(revenue?.average_order_value ?? 0).toLocaleString("en-IN")}`,
      sub: "Per successful order",
      icon: Target,
      color: "#a29bfe",
      bg: "rgba(162,155,254,0.1)",
    },
    {
      label: "AI-Assisted Revenue",
      value: `₹${(revenue?.ai_assisted_revenue ?? 0).toLocaleString("en-IN")}`,
      sub: "From AI shopping sessions",
      icon: Bot,
      color: "#6c5ce7",
      bg: "rgba(108,92,231,0.15)",
    },
  ];

  const typeColors: Record<string, { bg: string; color: string }> = {
    cross_sell: { bg: "rgba(0,184,148,0.1)", color: "#00b894" },
    upsell: { bg: "rgba(108,92,231,0.15)", color: "#a29bfe" },
    high_stock: { bg: "rgba(253,203,110,0.1)", color: "#fdcb6e" },
    high_demand: { bg: "rgba(116,185,255,0.1)", color: "#74b9ff" },
  };

  return (
    <AppLayout>
      <div className="page-header">
        <h1>Merchant Dashboard</h1>
        <p>AgentPay AI — AI-Powered Agentic Commerce for Modern Merchants</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : (
        <>
          {/* Stats */}
          <div className="stats-grid">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="stat-card">
                  <div className="stat-card-header">
                    <span className="stat-card-label">{stat.label}</span>
                    <div className="stat-card-icon" style={{ background: stat.bg }}>
                      <Icon size={18} style={{ color: stat.color }} />
                    </div>
                  </div>
                  <div className="stat-card-value">{stat.value}</div>
                  <div className="stat-card-sub">{stat.sub}</div>
                </div>
              );
            })}
          </div>

          {/* Growth Recommendations */}
          <div style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <Zap size={20} style={{ color: "#6c5ce7" }} />
              AI Growth Opportunities
            </h2>
            {growth.length > 0 ? (
              <div className="growth-grid">
                {growth.slice(0, 6).map((rec, i) => {
                  const tc = typeColors[rec.type] || typeColors.cross_sell;
                  return (
                    <div key={i} className="growth-card">
                      <span className="growth-card-type" style={{ background: tc.bg, color: tc.color }}>
                        {rec.type.replace("_", " ")}
                      </span>
                      <h3>{rec.title}</h3>
                      <p>{rec.description}</p>
                      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 8 }}>
                        📊 {rec.evidence}
                      </div>
                      <div className="growth-opportunity">
                        Estimated: ₹{rec.estimated_opportunity.toLocaleString("en-IN")}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                <Package size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
                <p>Growth recommendations will appear after you have order data.</p>
              </div>
            )}
          </div>

          {/* Recent Agent Actions */}
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              <Bot size={20} style={{ color: "#a29bfe" }} />
              Recent Agent Actions
            </h2>
            {actions.length > 0 ? (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Tool</th>
                      <th>Action</th>
                      <th>Status</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {actions.map((a) => (
                      <tr key={a.id}>
                        <td>{new Date(a.created_at).toLocaleTimeString()}</td>
                        <td><span className="badge badge-purple">{a.tool_name}</span></td>
                        <td>{a.action}</td>
                        <td>
                          <span className={`badge ${a.status === "success" ? "badge-success" : "badge-danger"}`}>
                            {a.status}
                          </span>
                        </td>
                        <td>{a.duration_ms ? `${a.duration_ms}ms` : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="card" style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                <Bot size={32} style={{ marginBottom: 12, opacity: 0.5 }} />
                <p>Agent actions will appear here after AI shopping sessions.</p>
              </div>
            )}
          </div>
        </>
      )}
    </AppLayout>
  );
}
