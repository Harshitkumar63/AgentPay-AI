"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Radio,
  RefreshCw,
  Play,
  CheckCircle,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { getWebhookEvents, simulateWebhook } from "@/services/api";
import { WebhookEvent } from "@/types";

export default function WebhookMonitorPage() {
  const [events, setEvents] = useState<WebhookEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simMessage, setSimMessage] = useState<string | null>(null);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const data = await getWebhookEvents(50);
      setEvents(data);
    } catch (err) {
      console.error("Failed to load webhooks", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const handleSimulate = async (type: string) => {
    setSimulating(true);
    setSimMessage(null);
    try {
      const res = await simulateWebhook(type);
      setSimMessage(
        `Webhook ${type} dispatched! Event ID: ${res.event_id} (Status: ${res.status})`
      );
      await fetchEvents();
    } catch (err: any) {
      setSimMessage(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Radio className="text-indigo-400 animate-pulse" />
            Webhook Event Monitor
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Real-time Razorpay webhook stream with HMAC signature verification and idempotency protection
          </p>
        </div>

        <button onClick={fetchEvents} className="btn btn-secondary btn-sm flex items-center gap-1">
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Interactive Simulation Panel for Buildathon Demonstrations (Phase 21) */}
      <div className="card mb-8 bg-gradient-to-r from-gray-900 to-indigo-950/40 border-indigo-500/30">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
              <Zap size={15} />
              Buildathon Webhook Test Controls
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              Simulate asynchronous payment gateway events to test ledger updates & duplicate protection
            </p>
          </div>
          <span className="badge badge-purple text-xs">Idempotency Active</span>
        </div>

        <div className="flex flex-wrap gap-3 mt-4">
          <button
            onClick={() => handleSimulate("payment.captured")}
            disabled={simulating}
            className="btn btn-sm btn-success flex items-center gap-1.5"
          >
            <Play size={13} />
            Simulate payment.captured
          </button>

          <button
            onClick={() => handleSimulate("payment.failed")}
            disabled={simulating}
            className="btn btn-sm btn-danger flex items-center gap-1.5"
          >
            <AlertTriangle size={13} />
            Simulate payment.failed
          </button>

          <button
            onClick={() => handleSimulate("payment.authorized")}
            disabled={simulating}
            className="btn btn-sm btn-secondary flex items-center gap-1.5"
          >
            <Play size={13} />
            Simulate payment.authorized
          </button>
        </div>

        {simMessage && (
          <div className="mt-3 p-2.5 rounded bg-black/40 border border-indigo-500/40 text-xs font-mono text-indigo-200">
            {simMessage}
          </div>
        )}
      </div>

      {/* Webhook Events Table */}
      <div className="card">
        <h3 className="text-base font-semibold mb-4 flex items-center justify-between">
          <span>Captured Gateway Webhooks</span>
          <span className="text-xs text-gray-400 font-normal">{events.length} total events recorded</span>
        </h3>

        {loading ? (
          <div className="loading">
            <div className="spinner" />
          </div>
        ) : events.length === 0 ? (
          <div className="empty-state">
            <Radio size={48} className="mx-auto mb-2 opacity-50" />
            <h3>No Webhook Events Recorded Yet</h3>
            <p className="text-xs">Trigger one of the simulation controls above or execute a checkout in the AI Shop.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Event Type</th>
                  <th>Event ID</th>
                  <th>Order ID</th>
                  <th>Payment ID</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((evt) => (
                  <tr key={evt.id}>
                    <td>
                      <span className="font-semibold text-sm text-gray-200 flex items-center gap-1.5">
                        {evt.status === "processed" && <CheckCircle size={14} className="text-emerald-400" />}
                        {evt.status === "ignored_duplicate" && (
                          <ShieldCheck size={14} className="text-amber-400" />
                        )}
                        {evt.status === "failed" && <XCircle size={14} className="text-rose-400" />}
                        {evt.event_type}
                      </span>
                    </td>
                    <td className="font-mono text-xs text-gray-400">{evt.event_id || "N/A"}</td>
                    <td className="font-mono text-xs text-indigo-300">{evt.order_id || "—"}</td>
                    <td className="font-mono text-xs text-gray-400">{evt.payment_id || "—"}</td>
                    <td>
                      <span
                        className={`badge ${
                          evt.status === "processed"
                            ? "badge-success"
                            : evt.status === "ignored_duplicate"
                            ? "badge-warning"
                            : "badge-danger"
                        }`}
                      >
                        {evt.status === "ignored_duplicate" ? "Idempotent Ignored" : evt.status}
                      </span>
                    </td>
                    <td className="text-xs text-gray-400">{new Date(evt.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
