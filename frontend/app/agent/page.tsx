"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Bot, ChevronDown, ChevronUp, Clock, Code, Layers, RefreshCw } from "lucide-react";
import { getAgentActions } from "@/services/api";
import type { AgentAction } from "@/types";

export default function AgentPage() {
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);
  const [expandedAction, setExpandedAction] = useState<string | null>(null);

  const fetchActions = () => {
    setLoading(true);
    getAgentActions(undefined, 100)
      .then((data) => {
        setActions(data);
        if (data.length > 0 && !expandedSession) {
          setExpandedSession(data[0].session_id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchActions();
  }, []);

  // Group actions by session
  const sessions = actions.reduce<Record<string, AgentAction[]>>((acc, a) => {
    if (!acc[a.session_id]) acc[a.session_id] = [];
    acc[a.session_id].push(a);
    return acc;
  }, {});

  return (
    <AppLayout>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="text-indigo-400" />
            Agent Execution Trace
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Complete inspectable trace of AI tool calls, input payloads, structured outputs, and latency
          </p>
        </div>

        <button onClick={fetchActions} className="btn btn-secondary btn-sm flex items-center gap-1">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>
      </div>

      {loading && actions.length === 0 ? (
        <div className="loading">
          <div className="spinner" />
        </div>
      ) : Object.keys(sessions).length === 0 ? (
        <div className="empty-state">
          <Bot size={48} className="mx-auto mb-2 opacity-50" />
          <h3>No Agent Traces Recorded Yet</h3>
          <p className="text-xs">
            Head over to the AI Shop and execute product searches or checkouts to see real-time tool traces.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(sessions).map(([sessionId, sessionActions]) => {
            const isSessionOpen = expandedSession === sessionId;
            const uniqueTools = [...new Set(sessionActions.map((a) => a.tool_name))];

            return (
              <div key={sessionId} className="card bg-gray-900/60 border-gray-800">
                <div
                  className="flex items-center justify-between cursor-pointer p-1"
                  onClick={() => setExpandedSession(isSessionOpen ? null : sessionId)}
                >
                  <div>
                    <h3 className="text-base font-semibold text-gray-200 flex items-center gap-2">
                      <Layers size={16} className="text-indigo-400" />
                      Session: <span className="font-mono text-sm text-indigo-300">{sessionId}</span>
                    </h3>
                    <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-2">
                      <span>{sessionActions.length} tool executions</span>
                      <span>•</span>
                      <span>{new Date(sessionActions[0].created_at).toLocaleString()}</span>
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="hidden sm:flex gap-1.5">
                      {uniqueTools.map((t) => (
                        <span key={t} className="badge badge-purple text-xs">
                          {t}
                        </span>
                      ))}
                    </div>
                    {isSessionOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </div>
                </div>

                {isSessionOpen && (
                  <div className="mt-4 pt-4 border-t border-gray-800 space-y-3">
                    {sessionActions
                      .sort(
                        (a, b) =>
                          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                      )
                      .map((action, idx) => {
                        const isActionOpen = expandedAction === action.id;

                        return (
                          <div
                            key={action.id}
                            className="p-3 rounded-lg bg-gray-950/80 border border-gray-800/80 text-xs"
                          >
                            <div
                              className="flex items-center justify-between cursor-pointer"
                              onClick={() => setExpandedAction(isActionOpen ? null : action.id)}
                            >
                              <div className="flex items-center gap-3">
                                <span className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-300 font-bold flex items-center justify-center text-[10px]">
                                  {idx + 1}
                                </span>
                                <span className="font-mono font-semibold text-indigo-300 text-sm">
                                  {action.tool_name}()
                                </span>
                                <span className="text-gray-400 hidden md:inline">
                                  {action.action}
                                </span>
                              </div>

                              <div className="flex items-center gap-3">
                                <span className="text-gray-500 font-mono flex items-center gap-1">
                                  <Clock size={11} />
                                  {action.duration_ms ? `${action.duration_ms}ms` : "—"}
                                </span>
                                <span
                                  className={`badge ${
                                    action.status === "success" ? "badge-success" : "badge-danger"
                                  }`}
                                >
                                  {action.status}
                                </span>
                              </div>
                            </div>

                            {/* Collapsible Input/Output Inspector */}
                            {isActionOpen && (
                              <div className="mt-3 pt-3 border-t border-gray-900 grid grid-cols-1 md:grid-cols-2 gap-3 font-mono">
                                <div>
                                  <span className="text-[11px] font-bold text-gray-400 block mb-1">
                                    INPUT ARGUMENTS:
                                  </span>
                                  <pre className="p-2 rounded bg-black/60 border border-gray-800 text-gray-300 overflow-x-auto text-[11px]">
                                    {JSON.stringify(action.input_data, null, 2)}
                                  </pre>
                                </div>

                                <div>
                                  <span className="text-[11px] font-bold text-gray-400 block mb-1">
                                    STRUCTURED TOOL OUTPUT:
                                  </span>
                                  <pre className="p-2 rounded bg-black/60 border border-gray-800 text-emerald-300 overflow-x-auto text-[11px]">
                                    {JSON.stringify(action.output_data, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </AppLayout>
  );
}
