"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  TrendingUp,
  Sparkles,
  Bot,
  ArrowUpRight,
  DollarSign,
  ShoppingCart,
  Send,
  CheckCircle,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
} from "lucide-react";
import {
  getGrowthRecommendations,
  getRevenueAnalytics,
  queryMerchantCopilot,
} from "@/services/api";
import { GrowthRecommendation, RevenueAnalytics, CopilotResponse } from "@/types";

export default function GrowthCenterPage() {
  const [recommendations, setRecommendations] = useState<GrowthRecommendation[]>([]);
  const [revenue, setRevenue] = useState<RevenueAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  // Copilot state
  const [query, setQuery] = useState("");
  const [copilotLoading, setCopilotLoading] = useState(false);
  const [copilotHistory, setCopilotHistory] = useState<
    { q: string; response: CopilotResponse }[]
  >([]);

  // Selected Campaign State
  const [approvedCampaigns, setApprovedCampaigns] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function loadData() {
      try {
        const [recsData, revData] = await Promise.all([
          getGrowthRecommendations("merchant_001"),
          getRevenueAnalytics("merchant_001", 30),
        ]);
        setRecommendations(recsData);
        setRevenue(revData);
      } catch (err) {
        console.error("Failed to load growth data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleCopilotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || copilotLoading) return;

    const currentQuery = query.trim();
    setQuery("");
    setCopilotLoading(true);

    try {
      const resp = await queryMerchantCopilot(currentQuery, "merchant_001");
      setCopilotHistory((prev) => [...prev, { q: currentQuery, response: resp }]);
    } catch (err) {
      console.error("Copilot query failed", err);
    } finally {
      setCopilotLoading(false);
    }
  };

  const askPreset = (preset: string) => {
    setQuery(preset);
  };

  const totalEstimatedOpportunity = recommendations.reduce(
    (sum, r) => sum + (r.estimated_opportunity || 0),
    0
  );

  return (
    <AppLayout>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <TrendingUp className="text-indigo-400" />
              AI Growth Center
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Autonomous catalog intelligence, cross-sell optimization, and Merchant AI Copilot
            </p>
          </div>
          <div className="badge badge-purple flex items-center gap-1">
            <Sparkles size={13} />
            <span>AI Driven Insights</span>
          </div>
        </div>
      </div>

      {/* Actual vs Estimated Distinction Banner (Phase 23) */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Actual Captured Revenue</span>
            <div className="stat-card-icon bg-emerald-500/10 text-emerald-400">
              <DollarSign size={18} />
            </div>
          </div>
          <div className="stat-card-value text-emerald-400">
            ₹{revenue?.total_revenue?.toLocaleString() || "0"}
          </div>
          <p className="stat-card-sub text-xs">Real database verified ledger</p>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">AI-Assisted Revenue</span>
            <div className="stat-card-icon bg-indigo-500/10 text-indigo-400">
              <Sparkles size={18} />
            </div>
          </div>
          <div className="stat-card-value text-indigo-400">
            ₹{revenue?.ai_assisted_revenue?.toLocaleString() || "0"}
          </div>
          <p className="stat-card-sub text-xs">Orders influenced by AI recommendations</p>
        </div>

        <div className="stat-card">
          <div className="stat-card-header">
            <span className="stat-card-label">Estimated Growth Opportunity</span>
            <div className="stat-card-icon bg-amber-500/10 text-amber-400">
              <ArrowUpRight size={18} />
            </div>
          </div>
          <div className="stat-card-value text-amber-400">
            ₹{totalEstimatedOpportunity.toLocaleString()}
          </div>
          <p className="stat-card-sub text-xs">
            Uncaptured potential from cross-sells & bundles
          </p>
        </div>
      </div>

      {/* Merchant AI Copilot (Phase 26) */}
      <div className="card mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Bot className="text-indigo-400" />
            Merchant AI Copilot
          </h2>
          <span className="text-xs text-gray-400">Grounded on real database analytics</span>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <span className="text-xs text-gray-400 self-center">Try asking:</span>
          {[
            "Why did revenue change this month?",
            "What products should I promote?",
            "What are my best cross-sell opportunities?",
          ].map((preset) => (
            <button
              key={preset}
              onClick={() => askPreset(preset)}
              className="btn btn-ghost btn-sm text-xs bg-gray-800/60 hover:bg-indigo-900/30"
            >
              {preset}
            </button>
          ))}
        </div>

        {/* Copilot Chat Feed */}
        <div className="space-y-4 max-h-96 overflow-y-auto mb-4 pr-2">
          {copilotHistory.length === 0 && (
            <div className="p-4 rounded-lg bg-gray-900/40 border border-gray-800 text-sm text-gray-400 flex items-start gap-3">
              <HelpCircle className="text-indigo-400 shrink-0 mt-0.5" size={18} />
              <div>
                <p className="font-medium text-gray-300">
                  Ask me anything about your revenue, conversions, inventory, and cross-sell potential.
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Answers are dynamically synthesized from your actual database orders and catalog telemetry.
                </p>
              </div>
            </div>
          )}

          {copilotHistory.map((item, idx) => (
            <div key={idx} className="space-y-3">
              <div className="chat-message user">
                <div className="chat-bubble">{item.q}</div>
              </div>
              <div className="chat-message ai">
                <div className="chat-avatar ai">
                  <Bot size={16} />
                </div>
                <div className="chat-bubble flex-1 space-y-3">
                  <p>{item.response.answer}</p>

                  {/* Suggested Actions */}
                  {item.response.suggested_actions?.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-800">
                      <p className="text-xs font-semibold text-gray-400 mb-1">
                        Recommended Actions:
                      </p>
                      <ul className="text-xs space-y-1 text-gray-300">
                        {item.response.suggested_actions.map((act, aIdx) => (
                          <li key={aIdx} className="flex items-center gap-1.5">
                            <CheckCircle size={12} className="text-emerald-400" />
                            {act}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Proposed Campaign Gated Card (Phase 27) */}
                  {item.response.proposed_campaign && (
                    <div className="mt-3 p-3 bg-gray-900/80 border border-indigo-500/30 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-indigo-300 uppercase tracking-wide flex items-center gap-1">
                          <Sparkles size={12} />
                          AI Campaign Proposal (Requires Approval)
                        </span>
                        <span className="risk-pill risk-high">High Risk</span>
                      </div>
                      <h4 className="font-semibold text-sm">
                        {item.response.proposed_campaign.title}
                      </h4>
                      <p className="text-xs text-gray-400 mt-1">
                        Offer {item.response.proposed_campaign.discount_percentage}% discount on{" "}
                        {item.response.proposed_campaign.product_name} (Budget: ₹
                        {item.response.proposed_campaign.budget})
                      </p>
                      <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-800">
                        <span className="text-xs text-emerald-400 font-semibold">
                          Est. Opportunity: ₹
                          {item.response.proposed_campaign.estimated_opportunity}
                        </span>
                        {approvedCampaigns[item.response.proposed_campaign.id] ? (
                          <span className="badge badge-success text-xs flex items-center gap-1">
                            <ShieldCheck size={12} /> Approved & Scheduled
                          </span>
                        ) : (
                          <button
                            onClick={() =>
                              setApprovedCampaigns((prev) => ({
                                ...prev,
                                [item.response.proposed_campaign!.id]: true,
                              }))
                            }
                            className="btn btn-primary btn-sm text-xs py-1"
                          >
                            Approve Campaign
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={handleCopilotSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask Copilot about your business performance, product stock, or growth ideas..."
            className="chat-input flex-1"
          />
          <button type="submit" disabled={copilotLoading} className="btn btn-primary">
            {copilotLoading ? (
              <span className="spinner w-4 h-4" />
            ) : (
              <>
                <Send size={15} />
                <span>Ask</span>
              </>
            )}
          </button>
        </form>
      </div>

      {/* Growth Opportunities Grid (Phase 23) */}
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Sparkles className="text-amber-400" />
        Catalog Growth & Cross-Sell Opportunities
      </h2>

      {loading ? (
        <div className="loading">
          <div className="spinner" />
        </div>
      ) : (
        <div className="growth-grid">
          {recommendations.map((rec, i) => (
            <div key={i} className="growth-card">
              <div className="flex justify-between items-start mb-2">
                <span
                  className={`growth-card-type ${
                    rec.type === "cross_sell"
                      ? "badge-purple"
                      : rec.type === "upsell"
                      ? "badge-info"
                      : "badge-warning"
                  }`}
                >
                  {rec.type.replace("_", " ")}
                </span>
                <span className="growth-opportunity">
                  +₹{rec.estimated_opportunity.toLocaleString()}
                </span>
              </div>
              <h3>{rec.title}</h3>
              <p>{rec.description}</p>
              <div className="text-xs text-gray-400 mb-3 bg-gray-900/50 p-2 rounded border border-gray-800">
                <strong>Evidence:</strong> {rec.evidence}
              </div>
              <div className="text-xs text-indigo-300 font-medium flex items-center gap-1">
                <ArrowUpRight size={13} />
                {rec.recommended_action}
              </div>
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
