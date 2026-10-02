"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Bell,
  CheckCircle,
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCheck,
  RefreshCw,
  Filter,
} from "lucide-react";
import { getNotifications, markNotificationRead, markAllNotificationsRead } from "@/services/api";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState<string>("");

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const data = await getNotifications(severityFilter || undefined);
      setNotifications(data);
    } catch (err) {
      console.error("Failed to load notifications:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [severityFilter]);

  const handleMarkRead = async (id: string) => {
    await markNotificationRead(id);
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsRead();
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const getSeverityIcon = (sev: string) => {
    switch (sev?.toUpperCase()) {
      case "CRITICAL":
        return <AlertOctagon size={18} className="text-red-400 shrink-0" />;
      case "HIGH":
        return <AlertTriangle size={18} className="text-amber-400 shrink-0" />;
      case "MEDIUM":
        return <Info size={18} className="text-blue-400 shrink-0" />;
      default:
        return <CheckCircle size={18} className="text-slate-400 shrink-0" />;
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex justify-between items-center flex-wrap gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <Bell size={24} className="text-amber-400" />
            <h1 className="text-2xl font-bold text-white">Notification & Security Alerts Center</h1>
          </div>
          <p className="text-slate-400 text-sm mt-1">
            Real-time feed of approval requests, policy violations, budget alerts, and circuit breaker events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleMarkAllRead}
            className="btn btn-secondary flex items-center gap-2 text-xs"
          >
            <CheckCheck size={14} /> Mark All as Read
          </button>
          <button
            onClick={loadNotifications}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-2 text-xs"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        {["", "HIGH", "MEDIUM", "LOW"].map((sev) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border ${
              severityFilter === sev
                ? "bg-blue-600 text-white border-blue-500"
                : "bg-slate-900/60 text-slate-400 border-slate-800 hover:text-white"
            }`}
          >
            {sev === "" ? "All Severities" : `${sev} Severity`}
          </button>
        ))}
      </div>

      {/* Notification List */}
      {loading && notifications.length === 0 ? (
        <div className="card text-center py-12">
          <RefreshCw size={32} className="animate-spin text-blue-400 mx-auto mb-3" />
          <p className="text-slate-400">Loading notifications...</p>
        </div>
      ) : notifications.length === 0 ? (
        <div className="card text-center py-12">
          <CheckCircle size={32} className="text-emerald-400 mx-auto mb-3" />
          <p className="text-slate-300 font-semibold">All clear — No active security alerts</p>
          <p className="text-xs text-slate-500 mt-1">All agent operations and risk checkpoints are within nominal thresholds.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`p-4 rounded-xl border flex items-start justify-between gap-4 transition-all ${
                n.read
                  ? "bg-slate-950/40 border-slate-900 text-slate-400"
                  : "bg-slate-900/80 border-slate-800 text-slate-100 shadow-md"
              }`}
            >
              <div className="flex items-start gap-3">
                {getSeverityIcon(n.severity)}
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-sm text-white">{n.title}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded font-mono bg-slate-800 border border-slate-700 text-slate-300">
                      {n.type}
                    </span>
                    {!n.read && (
                      <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    )}
                  </div>
                  <p className="text-xs text-slate-300 mt-1">{n.message}</p>
                  <div className="text-[11px] text-slate-500 mt-2 flex items-center gap-2">
                    <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                    {n.resource_id && <span>• Target: {n.resource_id}</span>}
                  </div>
                </div>
              </div>

              {!n.read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="btn btn-secondary text-xs px-2.5 py-1 whitespace-nowrap hover:text-white"
                >
                  Mark Read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
