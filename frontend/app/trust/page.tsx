"use client";

import AppLayout from "@/components/AppLayout";
import {
  ShieldCheck,
  Lock,
  Zap,
  Bot,
  FileCheck,
  Eye,
  CheckCircle2,
  Sliders,
  Radio,
  Server,
  Layers,
  Key,
} from "lucide-react";

export default function TrustCenterPage() {
  const pillars = [
    {
      title: "1. Payment & FinTech Security",
      icon: Lock,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      description: "Authoritative server-side price calculation and cryptographic payment validation.",
      points: [
        "Server-Side Price Recalculation: Client-supplied prices and totals are strictly ignored.",
        "Razorpay HMAC-SHA256 Signatures: End-to-end verification of checkout and webhook payloads.",
        "Idempotency Protection: Prevents duplicate charges via database unique keys.",
        "Air-Gapped Secrets: Payment secrets and API keys never leave server boundaries.",
      ],
    },
    {
      title: "2. Agent Governance & Spending Limits",
      icon: Bot,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/30",
      description: "Deterministic guardrails controlling autonomous agent purchasing capacity.",
      points: [
        "Granular Tool-Level Permissions: Agents are restricted strictly to declared capability scopes.",
        "Multi-Tier Budget Caps: Server-enforced daily limits, hourly limits, and per-transaction caps.",
        "Velocity Limiters: Halts automated runaway loops at 5 req/min and 20 req/hour.",
        "Automatic Circuit Breakers: Auto-pauses agents experiencing abnormal payment failure rates.",
      ],
    },
    {
      title: "3. AI Security & Prompt Injection Defense",
      icon: ShieldCheck,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      border: "border-purple-500/30",
      description: "Strict isolation ensuring untrusted text cannot override policy rules.",
      points: [
        "Input Sanitization & Data Delimitation: Untrusted catalog and user text cannot inject system instructions.",
        "Deterministic Policy Autorun: Rules and margins are evaluated in compiled Python code, not LLM prompts.",
        "No Direct Financial API Access: LLMs never directly interface with payment gateways.",
        "Human-in-the-Loop Approval Gating: 5-minute expiring authorization gates on all high-risk actions.",
      ],
    },
    {
      title: "4. Full Auditability & Decision Replay",
      icon: Eye,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/30",
      description: "Comprehensive transparency and cryptographic verification of all operations.",
      points: [
        "Persistent Audit Trail: Every discovery, policy check, approval, and webhook event is recorded.",
        "12-Stage Decision Replay: Step-by-step reconstruction of the exact governance path.",
        "Real-Time Event Stream: Low-latency telemetry monitoring agent tool executions.",
        "Zero Hallucination Grounding: Support responses and metrics query live database records.",
      ],
    },
  ];

  return (
    <AppLayout>
      <div className="page-header mb-8">
        <div className="flex items-center gap-2.5">
          <ShieldCheck size={28} className="text-emerald-400" />
          <h1 className="page-title text-2xl font-bold text-white">Trust & Governance Center</h1>
        </div>
        <p className="page-subtitle text-slate-400 text-sm mt-1">
          Architectural security boundaries, spending limits, policy invariants, and cryptographic compliance specifications.
        </p>
      </div>

      {/* Trust Pillars Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {pillars.map((p, i) => {
          const Icon = p.icon;
          return (
            <div key={i} className={`card border ${p.border} bg-slate-900/60 p-6 flex flex-col justify-between`}>
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <div className={`w-10 h-10 rounded-xl ${p.bg} ${p.color} flex items-center justify-center`}>
                    <Icon size={20} />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white">{p.title}</h2>
                    <p className="text-xs text-slate-400">{p.description}</p>
                  </div>
                </div>

                <div className="space-y-2.5 mt-4 pt-4 border-t border-slate-800">
                  {p.points.map((pt, j) => (
                    <div key={j} className="flex items-start gap-2.5 text-xs text-slate-300">
                      <CheckCircle2 size={15} className={`${p.color} shrink-0 mt-0.5`} />
                      <span className="leading-relaxed">{pt}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Security Architecture Flowchart */}
      <div className="card p-6 bg-slate-900/80 border border-slate-800">
        <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2">
          <Layers size={18} className="text-blue-400" />
          Security Boundary Isolation Model
        </h3>
        <p className="text-xs text-slate-400 mb-6">
          Every transaction must sequentially pass all 8 authoritative backend gates before funds or orders can be committed.
        </p>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs font-mono">
          {[
            { step: "1. LLM Prompt", sub: "Untrusted" },
            { step: "2. Tool Boundary", sub: "Sanitized" },
            { step: "3. Permissions", sub: "Authoritative" },
            { step: "4. Policy Engine", sub: "Deterministic" },
            { step: "5. Risk Engine", sub: "Scored" },
            { step: "6. Budget & Trust", sub: "Gated" },
            { step: "7. Human Approval", sub: "5-Min TTL" },
            { step: "8. Razorpay", sub: "Captured" },
          ].map((item, idx) => (
            <div key={idx} className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex flex-col justify-center">
              <div className="font-bold text-white text-[11px]">{item.step}</div>
              <div className="text-[10px] text-blue-400 mt-1">{item.sub}</div>
            </div>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
