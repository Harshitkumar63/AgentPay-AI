"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import {
  Bot,
  Shield,
  Key,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  PauseCircle,
  PlayCircle,
  ArrowLeft,
  DollarSign,
  Activity,
  Zap,
  Lock,
} from "lucide-react";
import { rotateAgentKey, pauseAgent, resumeAgent } from "@/services/api";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params?.id as string;

  const [agent, setAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [rotatedKey, setRotatedKey] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadAgent = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://localhost:8000/api/admin/agents/${agentId}`);
      if (res.ok) {
        const data = await res.json();
        setAgent(data);
      }
    } catch (err) {
      console.error("Failed to load agent:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (agentId) {
      loadAgent();
    }
  }, [agentId]);

  const handleRotateKey = async () => {
    if (!confirm(`Are you sure you want to rotate the API key for ${agent?.name}? Any client using the old key will be disconnected.`)) {
      return;
    }
    try {
      setActionLoading(true);
      const res = await rotateAgentKey(agentId);
      setRotatedKey(res.api_key);
      await loadAgent();
    } catch (err: any) {
      alert(`Key rotation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleTogglePause = async () => {
    try {
      setActionLoading(true);
      if (agent?.status === "ACTIVE") {
        await pauseAgent(agentId, "Paused by merchant admin");
      } else {
        await resumeAgent(agentId, "Resumed by merchant admin");
      }
      await loadAgent();
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !agent) {
    return (
      <AppLayout>
        <div className="card text-center py-12">
          <RefreshCw size={32} className="animate-spin text-blue-400 mx-auto mb-3" />
          <p className="text-slate-400">Loading Agent Details...</p>
        </div>
      </AppLayout>
    );
  }

  if (!agent) {
    return (
      <AppLayout>
        <div className="card text-center py-12">
          <AlertTriangle size={32} className="text-amber-400 mx-auto mb-3" />
          <p className="text-slate-400">Agent not found in registry.</p>
          <Link href="/agents" className="btn btn-secondary mt-4 inline-flex items-center gap-2">
            <ArrowLeft size={16} /> Back to Registry
          </Link>
        </div>
      </AppLayout>
    );
  }

  const isPaused = agent.status === "PAUSED";
  const isTripped = agent.circuit_breaker_tripped;

  return (
    <AppLayout>
      <div className="mb-6 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Link href="/agents" className="btn btn-secondary p-2 rounded-lg">
            <ArrowLeft size={18} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <Bot size={24} className="text-blue-400" />
              <h1 className="text-2xl font-bold text-white">{agent.name}</h1>
              <span className={`badge ${isPaused ? "badge-warning" : "badge-success"}`}>
                {agent.status}
              </span>
            </div>
            <p className="text-slate-400 text-sm mt-0.5">{agent.description || "Registered autonomous AI agent"}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleTogglePause}
            disabled={actionLoading}
            className={`btn flex items-center gap-2 ${
              isPaused ? "btn-primary bg-emerald-600 hover:bg-emerald-500" : "btn-secondary bg-amber-950/60 text-amber-300 border-amber-800"
            }`}
          >
            {isPaused ? <PlayCircle size={16} /> : <PauseCircle size={16} />}
            {isPaused ? "Resume Agent" : "Emergency Pause"}
          </button>

          <button
            onClick={handleRotateKey}
            disabled={actionLoading}
            className="btn btn-secondary flex items-center gap-2 border-indigo-800/80 text-indigo-300 hover:bg-indigo-950/40"
          >
            <Key size={16} />
            Rotate API Key
          </button>
        </div>
      </div>

      {rotatedKey && (
        <div className="p-4 rounded-xl border border-indigo-500/50 bg-indigo-950/40 text-indigo-200 mb-6">
          <div className="flex items-center gap-2 font-semibold text-white mb-1">
            <Key size={18} className="text-indigo-400" />
            New API Key Generated
          </div>
          <p className="text-xs text-indigo-300 mb-2">
            Copy and store this API key now. It is hashed in the database and will NOT be shown again.
          </p>
          <div className="bg-slate-950 p-3 rounded font-mono text-sm border border-indigo-900/60 text-emerald-400 select-all">
            {rotatedKey}
          </div>
        </div>
      )}

      {/* Grid of Key Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Shield size={14} className="text-blue-400" /> Trust Score
          </div>
          <div className="text-2xl font-bold text-white">{agent.trust_score}/100</div>
          <div className="text-xs text-slate-500 mt-1">Tier: {agent.trust_score >= 90 ? "Trusted (₹10k Limit)" : "Standard"}</div>
        </div>

        <div className="card">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <DollarSign size={14} className="text-emerald-400" /> Daily Spending Limit
          </div>
          <div className="text-2xl font-bold text-white">₹{agent.daily_budget?.toLocaleString("en-IN")}</div>
          <div className="text-xs text-slate-500 mt-1">Max Tx: ₹{agent.per_transaction_limit?.toLocaleString("en-IN")}</div>
        </div>

        <div className="card">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Zap size={14} className="text-amber-400" /> Circuit Breaker
          </div>
          <div className="text-2xl font-bold text-white">{agent.circuit_breaker_state || "CLOSED"}</div>
          <div className={`text-xs mt-1 ${isTripped ? "text-red-400" : "text-emerald-400"}`}>
            {isTripped ? "Tripped (Tripped state)" : "Normal Operation"}
          </div>
        </div>

        <div className="card">
          <div className="text-xs text-slate-400 mb-1 flex items-center gap-1.5">
            <Key size={14} className="text-purple-400" /> Key Hash Prefix
          </div>
          <div className="text-xl font-mono font-bold text-white">{agent.api_key_prefix || "agp_..."}</div>
          <div className="text-xs text-slate-500 mt-1">Hashed SHA-256 in DB</div>
        </div>
      </div>

      {/* Permissions and Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <Lock size={18} className="text-blue-400" /> Scoped Granular Permissions
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Only explicit permissions authorized below will allow tool execution.
          </p>
          <div className="flex flex-wrap gap-2">
            {(agent.permissions || []).map((perm: string) => (
              <span
                key={perm}
                className="px-2.5 py-1 rounded-md text-xs font-mono bg-blue-950/60 border border-blue-800/60 text-blue-300"
              >
                {perm}
              </span>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
            <Activity size={18} className="text-purple-400" /> Operational Metadata
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Agent ID:</span>
              <span className="font-mono text-slate-200">{agent.id}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Owner:</span>
              <span className="text-slate-200">{agent.owner}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Role:</span>
              <span className="text-slate-200">{agent.role}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800">
              <span className="text-slate-400">Created At:</span>
              <span className="text-slate-200">{new Date(agent.created_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Last Activity:</span>
              <span className="text-slate-200">{new Date(agent.last_activity).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
