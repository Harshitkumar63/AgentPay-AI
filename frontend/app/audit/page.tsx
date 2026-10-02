"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Shield, ChevronDown, ChevronUp, CheckCircle, AlertCircle, RefreshCw, Lock, Link as LinkIcon } from "lucide-react";
import { getAuditLogs, verifyAuditTrail } from "@/services/api";
import type { AuditLog } from "@/types";

const resultColors: Record<string, string> = {
  SUCCESS: "badge-success",
  FAILURE: "badge-danger",
  PENDING: "badge-warning",
  ALLOWED: "badge-success",
  BLOCKED: "badge-danger",
  APPROVED: "badge-success",
  REJECTED: "badge-danger",
  AUTO_APPROVED: "badge-info",
};

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean;
    events_checked: number;
    broken_at?: string;
    root_hash?: string;
  } | null>(null);

  const loadLogs = () => {
    setLoading(true);
    getAuditLogs(100)
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleVerifyTrail = async () => {
    try {
      setVerifying(true);
      const res = await verifyAuditTrail();
      setVerificationResult(res);
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex justify-between items-center flex-wrap gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <Shield size={28} className="text-emerald-400" />
            <h1 className="text-2xl font-bold text-white">Tamper-Evident Audit Trail</h1>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Cryptographic SHA-256 hash-chained log of all agent decisions and financial fund movements.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleVerifyTrail}
            disabled={verifying}
            className="btn btn-primary flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500"
          >
            <Lock size={16} />
            {verifying ? "Verifying Hash Chain..." : "Verify Hash Chain Integrity"}
          </button>
          <button onClick={loadLogs} disabled={loading} className="btn btn-secondary flex items-center gap-2">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {verificationResult && (
        <div
          className={`p-4 rounded-xl border mb-6 flex items-start gap-3 ${
            verificationResult.valid
              ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-200"
              : "bg-red-950/40 border-red-500/50 text-red-200"
          }`}
        >
          {verificationResult.valid ? (
            <CheckCircle className="text-emerald-400 shrink-0 mt-0.5" size={20} />
          ) : (
            <AlertCircle className="text-red-400 shrink-0 mt-0.5" size={20} />
          )}
          <div>
            <h3 className="font-semibold">
              {verificationResult.valid
                ? `Audit Chain Valid: ${verificationResult.events_checked} Events Cryptographically Verified`
                : "Tamper Detected! Cryptographic Chain Integrity Broken"}
            </h3>
            <p className="text-xs opacity-90 mt-1">
              {verificationResult.valid
                ? `Every entry from Genesis Hash is mathematically validated with un-tampered parent links.`
                : `Integrity check failed at entry ID: ${verificationResult.broken_at || "Unknown"}`}
            </p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : logs.length === 0 ? (
        <div className="empty-state">
          <Shield size={48} />
          <h3>No audit logs yet</h3>
          <p>Audit entries will appear as financial actions are performed.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Amount</th>
                <th>Policy</th>
                <th>Approval</th>
                <th>Result</th>
                <th>Event Hash</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log: any) => (
                <>
                  <tr key={log.id} onClick={() => setExpanded(expanded === log.id ? null : log.id)} style={{ cursor: "pointer" }}>
                    <td style={{ fontSize: 13 }}>{new Date(log.created_at).toLocaleTimeString()}</td>
                    <td>
                      <span className="badge badge-purple">{log.actor_type}</span>
                      <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{log.actor_id}</div>
                    </td>
                    <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{log.action}</td>
                    <td>
                      {log.resource_type && <span className="badge badge-info">{log.resource_type}</span>}
                      {log.resource_id && <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{log.resource_id}</div>}
                    </td>
                    <td>{log.amount ? `₹${log.amount.toLocaleString("en-IN")}` : "—"}</td>
                    <td>{log.policy_result ? <span className={`badge ${resultColors[log.policy_result] || ""}`}>{log.policy_result}</span> : "—"}</td>
                    <td>{log.approval_status ? <span className={`badge ${resultColors[log.approval_status] || ""}`}>{log.approval_status}</span> : "—"}</td>
                    <td>{log.result ? <span className={`badge ${resultColors[log.result] || ""}`}>{log.result}</span> : "—"}</td>
                    <td>
                      <code className="text-[11px] text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                        {log.event_hash ? log.event_hash.substring(0, 10) + "..." : "sha256"}
                      </code>
                    </td>
                    <td>{expanded === log.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</td>
                  </tr>
                  {expanded === log.id && (
                    <tr key={`${log.id}-detail`}>
                      <td colSpan={10} style={{ background: "var(--bg-surface)", padding: 20 }}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                          <div>
                            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Reason</div>
                            <div style={{ fontSize: 14 }}>{log.reason || "—"}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Full Timestamp</div>
                            <div style={{ fontSize: 14 }}>{new Date(log.created_at).toLocaleString()}</div>
                          </div>
                          <div style={{ gridColumn: "1 / -1" }}>
                            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Cryptographic Hash Chaining</div>
                            <div className="bg-slate-950 p-3 rounded border border-slate-800 text-xs font-mono text-slate-300 flex flex-col gap-1">
                              <div><span className="text-slate-500">Event Hash:</span> {log.event_hash || "N/A"}</div>
                              <div><span className="text-slate-500">Parent Hash:</span> {log.previous_hash || "Genesis Hash (0000...)"}</div>
                              {log.request_id && <div><span className="text-slate-500">Request Correlation ID:</span> {log.request_id}</div>}
                            </div>
                          </div>
                          {Object.keys(log.metadata_extra || {}).length > 0 && (
                            <div style={{ gridColumn: "1 / -1" }}>
                              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Metadata</div>
                              <pre style={{ fontSize: 12, background: "var(--bg-primary)", padding: 12, borderRadius: 8, overflow: "auto", color: "var(--text-secondary)" }}>
                                {JSON.stringify(log.metadata_extra, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}
