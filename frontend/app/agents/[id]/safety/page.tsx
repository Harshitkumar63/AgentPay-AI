"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import {
  Award,
  ShieldCheck,
  ShieldAlert,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Zap,
  Info,
} from "lucide-react";
import { getAgentSafetyCertification } from "@/services/api";
import { AgentSafetyReport } from "@/types";

export default function AgentSafetyPage() {
  const params = useParams();
  const agentId = (params?.id as string) || "ShoppingBot";
  const [report, setReport] = useState<AgentSafetyReport | null>(null);
  const [loading, setLoading] = useState(true);

  const runAudit = async () => {
    try {
      setLoading(true);
      const data = await getAgentSafetyCertification(agentId);
      setReport(data);
    } catch (err) {
      console.error("Safety audit failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runAudit();
  }, [agentId]);

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <Link href="/agents" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-3">
          <ArrowLeft size={14} /> Back to Agent Registry
        </Link>
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <Award size={26} className="text-amber-400" />
              <h1 className="page-title text-2xl font-bold text-white">
                Agent Safety Certification — {agentId}
              </h1>
            </div>
            <p className="page-subtitle text-slate-400 text-sm mt-1">
              Automated 10-point governance verification evaluating boundary enforcement and spending defense.
            </p>
          </div>
          <button
            onClick={runAudit}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Re-run Safety Audit
          </button>
        </div>
      </div>

      {loading && !report ? (
        <div className="card text-center py-16">
          <RefreshCw size={36} className="animate-spin text-blue-400 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">Executing 10 Deterministic Safety Checks...</p>
          <p className="text-xs text-slate-500 mt-1">Auditing spending limits, tool permissions, and injection defenses</p>
        </div>
      ) : report ? (
        <div className="space-y-6">
          {/* Certificate Banner Card */}
          <div className="card bg-gradient-to-r from-slate-900 via-slate-900 to-blue-950/40 border border-blue-500/30 p-6 relative overflow-hidden">
            <div className="flex flex-wrap justify-between items-center gap-6">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge badge-success px-3 py-1 text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded-full flex items-center gap-1.5">
                    <ShieldCheck size={14} />
                    {report.status}
                  </span>
                  <span className="text-xs text-slate-400">Target: {report.agent_name}</span>
                </div>
                <h2 className="text-3xl font-extrabold text-white mt-2">
                  Safety Score: {report.safety_score} <span className="text-slate-500 text-xl font-normal">/ 100</span>
                </h2>
                <p className="text-xs text-slate-400 max-w-xl mt-2">{report.disclaimer}</p>
              </div>

              <div className="flex flex-col items-center justify-center p-4 bg-slate-950/80 rounded-2xl border border-slate-800 text-center min-w-[140px]">
                <div className="text-3xl font-black text-blue-400">
                  {report.checks.filter((c) => c.passed).length}/10
                </div>
                <div className="text-[11px] text-slate-400 font-semibold uppercase mt-1">Gating Checks Passed</div>
              </div>
            </div>
          </div>

          {/* 10 Automated Check Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.checks.map((c, i) => (
              <div
                key={i}
                className={`card p-4 flex items-start justify-between gap-3 border ${
                  c.passed
                    ? "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                    : "bg-red-950/15 border-red-500/40"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                    c.passed ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
                  }`}>
                    {c.passed ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                  </div>
                  <div>
                    <div className="text-sm font-bold text-white flex items-center gap-2">
                      <span>{i + 1}. {c.check_name}</span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1 leading-relaxed">{c.details}</div>
                  </div>
                </div>
                <span className={`text-xs font-mono font-bold shrink-0 ${c.passed ? "text-emerald-400" : "text-red-400"}`}>
                  +{c.score_points} pts
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </AppLayout>
  );
}
