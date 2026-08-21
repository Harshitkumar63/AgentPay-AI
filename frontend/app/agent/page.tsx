"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Bot } from "lucide-react";
import { getAgentActions } from "@/services/api";
import type { AgentAction } from "@/types";

export default function AgentPage() {
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getAgentActions(undefined, 100)
      .then(setActions)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Group by session
  const sessions = actions.reduce<Record<string, AgentAction[]>>((acc, a) => {
    if (!acc[a.session_id]) acc[a.session_id] = [];
    acc[a.session_id].push(a);
    return acc;
  }, {});

  return (
    <AppLayout>
      <div className="page-header">
        <h1><Bot size={28} style={{ display: "inline", marginRight: 10, verticalAlign: "middle" }} />Agent Activity</h1>
        <p>Trace all AI agent tool calls and reasoning steps • {actions.length} actions</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : Object.keys(sessions).length === 0 ? (
        <div className="empty-state">
          <Bot size={48} />
          <h3>No agent activity yet</h3>
          <p>Start a conversation in the AI Shop to see agent traces here.</p>
        </div>
      ) : (
        <div>
          {Object.entries(sessions).map(([sessionId, sessionActions]) => (
            <div key={sessionId} className="card" style={{ marginBottom: 16 }}>
              <div
                style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer", marginBottom: expanded === sessionId ? 16 : 0 }}
                onClick={() => setExpanded(expanded === sessionId ? null : sessionId)}
              >
                <div>
                  <h3 style={{ fontSize: 15, fontWeight: 600 }}>Session: {sessionId}</h3>
                  <p style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {sessionActions.length} tool calls • {new Date(sessionActions[sessionActions.length - 1].created_at).toLocaleString()}
                  </p>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  {[...new Set(sessionActions.map((a) => a.tool_name))].map((t) => (
                    <span key={t} className="badge badge-purple">{t}</span>
                  ))}
                </div>
              </div>

              {expanded === sessionId && (
                <div>
                  {sessionActions.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()).map((action, i) => (
                    <div key={action.id} className="agent-step" style={{ marginBottom: 8 }}>
                      <div className="agent-step-number">{i + 1}</div>
                      <span className="agent-step-tool">{action.tool_name}</span>
                      <span style={{ color: "var(--text-secondary)", flex: 1 }}>{action.action}</span>
                      <span className={`badge ${action.status === "success" ? "badge-success" : "badge-danger"}`}>
                        {action.status}
                      </span>
                      <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                        {action.duration_ms ? `${action.duration_ms}ms` : ""}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
