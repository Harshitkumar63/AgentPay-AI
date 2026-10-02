"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import {
  Bot,
  Shield,
  Zap,
  AlertTriangle,
  CheckCircle2,
  PauseCircle,
  XCircle,
  RefreshCw,
  Award,
  Sliders,
  DollarSign,
  Activity,
} from "lucide-react";
import { getAgents, setAgentStatus } from "@/services/api";
import { AgentRegistryItem } from "@/types";

export default function AgentsRegistryPage() {
  const [agents, setAgents] = useState<AgentRegistryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  const loadAgents = async () => {
    try {
      setLoading(true);
      const data = await getAgents();
      setAgents(data);
    } catch (err) {
      console.error("Failed to load agents:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleStatusChange = async (agentId: string, status: "ACTIVE" | "PAUSED" | "DISABLED") => {
    try {
      setUpdatingId(agentId);
      await setAgentStatus(agentId, status, `Manual status change via dashboard`);
      await loadAgents();
    } catch (err: any) {
      alert(err.message || "Failed to update agent status");
    } finally {
      setUpdatingId(null);
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex justify-between items-center flex-wrap gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <Bot size={24} className="text-blue-400" />
            <h1 className="page-title text-2xl font-bold text-white">Multi-Agent Registry & Governance</h1>
          </div>
          <p className="page-subtitle text-slate-400 text-sm mt-1">
            Deterministic tool permissions, spending limits, velocity guards, circuit breakers, and Emergency Kill Switches.
          </p>
        </div>
        <button
          onClick={loadAgents}
          className="btn btn-secondary flex items-center gap-2"
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh Registry
        </button>
      </div>

      {loading && agents.length === 0 ? (
        <div className="card text-center py-12">
          <RefreshCw size={32} className="animate-spin text-blue-400 mx-auto mb-3" />
          <p className="text-slate-400">Loading Agent Registry...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => {
            const isTripped = agent.circuit_breaker_tripped;
            const isPaused = agent.status === "PAUSED";
            const isDisabled = agent.status === "DISABLED";
            const isActive = agent.status === "ACTIVE";

            return (
              <div
                key={agent.id}
                className={`card relative overflow-hidden flex flex-col justify-between border ${
                  isTripped || isDisabled
                    ? "border-red-500/50 bg-red-950/10"
                    : isPaused
                    ? "border-amber-500/50 bg-amber-950/10"
                    : "border-slate-800 bg-slate-900/60"
                }`}
              >
                {/* Status Indicator */}
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                      <Bot size={20} />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-white leading-tight">{agent.name}</h2>
                      <span className="text-xs font-mono text-slate-400">ID: {agent.id}</span>
                    </div>
                  </div>

                  <span
                    className={`badge font-semibold text-xs px-2.5 py-1 rounded-full ${
                      isActive
                        ? "badge-success bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                        : isPaused
                        ? "badge-warning bg-amber-500/10 text-amber-400 border border-amber-500/30"
                        : "badge-danger bg-red-500/10 text-red-400 border border-red-500/30"
                    }`}
                  >
                    {agent.status}
                  </span>
                </div>

                <p className="text-xs text-slate-400 mb-4 line-clamp-2">{agent.description}</p>

                {/* Circuit breaker alert if tripped */}
                {isTripped && (
                  <div className="mb-4 p-3 rounded-lg bg-red-500/15 border border-red-500/30 flex items-start gap-2">
                    <AlertTriangle size={16} className="text-red-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-bold text-red-300">Circuit Breaker Tripped</div>
                      <div className="text-xs text-red-400/90">{agent.circuit_breaker_reason || "Unusual failure rate detected"}</div>
                    </div>
                  </div>
                )}

                {/* Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 mb-4 text-center">
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-semibold">Trust Score</div>
                    <div className="text-sm font-bold text-emerald-400">{agent.trust_score}/100</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-semibold">Daily Cap</div>
                    <div className="text-sm font-bold text-white">₹{agent.daily_budget ? agent.daily_budget.toLocaleString() : "0"}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase font-semibold">Per-Tx Cap</div>
                    <div className="text-sm font-bold text-blue-400">₹{agent.per_transaction_limit ? agent.per_transaction_limit.toLocaleString() : "0"}</div>
                  </div>
                </div>

                {/* Permissions Badges */}
                <div className="mb-4">
                  <div className="text-xs font-semibold text-slate-400 mb-1.5 flex items-center gap-1">
                    <Shield size={13} className="text-slate-500" />
                    Granted Permissions
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {(agent.permissions || []).map((perm) => (
                      <span
                        key={perm}
                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/50"
                      >
                        {perm}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Governance Controls & Actions */}
                <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2 flex-wrap">
                  <Link
                    href={`/agents/${agent.id}/safety`}
                    className="btn btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 text-blue-300"
                  >
                    <Award size={14} className="text-blue-400" />
                    Safety Audit
                  </Link>

                  {/* Kill Switch Actions */}
                  <div className="flex items-center gap-1.5">
                    {isActive ? (
                      <>
                        <button
                          onClick={() => handleStatusChange(agent.id, "PAUSED")}
                          disabled={updatingId === agent.id}
                          className="btn btn-secondary text-xs py-1.5 px-2.5 text-amber-400 hover:bg-amber-500/10"
                          title="Pause agent financial transactions"
                        >
                          <PauseCircle size={14} />
                          Pause
                        </button>
                        <button
                          onClick={() => handleStatusChange(agent.id, "DISABLED")}
                          disabled={updatingId === agent.id}
                          className="btn btn-danger text-xs py-1.5 px-2.5"
                          title="Emergency kill switch: Disable agent"
                        >
                          <XCircle size={14} />
                          Kill
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleStatusChange(agent.id, "ACTIVE")}
                        disabled={updatingId === agent.id}
                        className="btn btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
                      >
                        <CheckCircle2 size={14} />
                        Reactivate
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </AppLayout>
  );
}
