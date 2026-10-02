"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Activity,
  Zap,
  RefreshCw,
  Clock,
  DollarSign,
  TrendingUp,
  Shield,
  Bot,
  Filter,
} from "lucide-react";
import { getLiveEvents, getObservabilityMetrics } from "@/services/api";
import { LiveEventItem, ObservabilityMetrics } from "@/types";

export default function LiveStreamPage() {
  const [events, setEvents] = useState<LiveEventItem[]>([]);
  const [metrics, setMetrics] = useState<ObservabilityMetrics | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(false);
  const [selectedFilter, setSelectedFilter] = useState("ALL");

  const fetchData = async () => {
    try {
      setLoading(true);
      const [evData, metData] = await Promise.all([
        getLiveEvents(40),
        getObservabilityMetrics(),
      ]);
      setEvents(evData.events || []);
      setMetrics(metData);
    } catch (err) {
      console.error("Failed to load live events:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    let timer: any;
    if (autoRefresh) {
      timer = setInterval(fetchData, 4000);
    }
    return () => clearInterval(timer);
  }, [autoRefresh]);

  const filteredEvents = events.filter((e) => {
    if (selectedFilter === "ALL") return true;
    if (selectedFilter === "PAYMENTS") return e.event_type.includes("PAYMENT") || e.event_type.includes("ORDER");
    if (selectedFilter === "GOVERNANCE") return e.policy_result || e.event_type.includes("POLICY") || e.event_type.includes("AGENT");
    if (selectedFilter === "AI") return e.actor_type === "ai_agent";
    return true;
  });

  return (
    <AppLayout>
      <div className="page-header mb-6 flex justify-between items-center flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity size={24} className="text-blue-400 animate-pulse" />
            <h1 className="page-title text-2xl font-bold text-white">Live Agent Event Stream & Observability</h1>
          </div>
          <p className="page-subtitle text-slate-400 text-sm mt-1">
            Real-time telemetry monitoring multi-agent tool calls, policy evaluations, and payment captures.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-300 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="accent-blue-500 rounded"
            />
            <span>Auto-refresh (4s)</span>
          </label>
          <button
            onClick={fetchData}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Latency & AI Cost Metrics */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
          <div className="card p-3 bg-slate-900/60 border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Agent Response</div>
            <div className="text-base font-bold text-blue-400 mt-0.5">{metrics.avg_agent_response_ms}ms</div>
          </div>
          <div className="card p-3 bg-slate-900/60 border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Tool Latency</div>
            <div className="text-base font-bold text-cyan-400 mt-0.5">{metrics.avg_tool_latency_ms}ms</div>
          </div>
          <div className="card p-3 bg-slate-900/60 border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Payment Gateway</div>
            <div className="text-base font-bold text-emerald-400 mt-0.5">{metrics.avg_payment_latency_ms}ms</div>
          </div>
          <div className="card p-3 bg-slate-900/60 border border-slate-800 text-center">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">Est. AI Cost</div>
            <div className="text-base font-bold text-amber-400 mt-0.5">₹{metrics.estimated_ai_cost_inr.toFixed(2)}</div>
          </div>
          <div className="card p-3 bg-slate-900/60 border border-slate-800 text-center col-span-2 sm:col-span-1">
            <div className="text-[10px] text-slate-500 uppercase font-semibold">AI Commercial ROI</div>
            <div className="text-base font-bold text-emerald-400 mt-0.5">+{metrics.ai_roi_percentage.toLocaleString()}%</div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-4">
        {["ALL", "PAYMENTS", "GOVERNANCE", "AI"].map((f) => (
          <button
            key={f}
            onClick={() => setSelectedFilter(f)}
            className={`text-xs px-3 py-1.5 rounded-lg border font-semibold transition-all ${
              selectedFilter === f
                ? "bg-blue-600 border-blue-500 text-white"
                : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Event Stream List */}
      <div className="card overflow-hidden p-0">
        <div className="p-3.5 bg-slate-950/80 border-b border-slate-800 flex justify-between items-center text-xs font-semibold text-slate-400">
          <span>Captured Telemetry Events ({filteredEvents.length})</span>
          <span className="font-mono text-[11px] text-slate-500">Live Socket Buffer</span>
        </div>

        <div className="divide-y divide-slate-800/60 max-h-[550px] overflow-y-auto font-mono text-xs">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-16 text-slate-500 font-sans">No recent telemetry events</div>
          ) : (
            filteredEvents.map((e) => (
              <div key={e.id} className="p-3.5 hover:bg-slate-800/30 transition-colors flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-3 min-w-[240px]">
                  <span className="text-[10px] text-slate-500 shrink-0">
                    {e.timestamp ? e.timestamp.slice(11, 19) : "--:--:--"}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    e.actor_type === "ai_agent" ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                  }`}>
                    {e.actor}
                  </span>
                  <span className="text-white font-bold">{e.event_type}</span>
                </div>

                <div className="flex items-center gap-3 text-slate-400 text-xs">
                  {e.amount && (
                    <span className="text-white font-bold">₹{e.amount.toLocaleString()}</span>
                  )}
                  {e.policy_result && (
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      e.policy_result === "ALLOWED" ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                    }`}>
                      {e.policy_result}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </AppLayout>
  );
}
