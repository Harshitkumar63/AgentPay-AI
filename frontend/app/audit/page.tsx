"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Shield, ChevronDown, ChevronUp } from "lucide-react";
import { getAuditLogs } from "@/services/api";
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

  useEffect(() => {
    getAuditLogs(100)
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="page-header">
        <h1><Shield size={28} style={{ display: "inline", marginRight: 10, verticalAlign: "middle" }} />Audit Logs</h1>
        <p>Complete trail of all financial actions and agent operations • {logs.length} entries</p>
      </div>

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
                <th></th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
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
                    <td>{expanded === log.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}</td>
                  </tr>
                  {expanded === log.id && (
                    <tr key={`${log.id}-detail`}>
                      <td colSpan={9} style={{ background: "var(--bg-surface)", padding: 20 }}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                          <div>
                            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Reason</div>
                            <div style={{ fontSize: 14 }}>{log.reason || "—"}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>Full Timestamp</div>
                            <div style={{ fontSize: 14 }}>{new Date(log.created_at).toLocaleString()}</div>
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
