"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  History,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Shield,
  CreditCard,
  Radio,
  FileText,
  Search,
  ExternalLink,
} from "lucide-react";
import { getOrders, getDecisionReplay } from "@/services/api";
import { Order, DecisionReplayData } from "@/types";

export default function DecisionReplayPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [replayData, setReplayData] = useState<DecisionReplayData | null>(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingReplay, setLoadingReplay] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        setLoadingList(true);
        const data = await getOrders();
        setOrders(data);
        if (data.length > 0) {
          setSelectedOrderId(data[0].id);
        }
      } catch (err) {
        console.error("Failed to load orders for replay:", err);
      } finally {
        setLoadingList(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    if (!selectedOrderId) return;
    async function loadReplay() {
      try {
        setLoadingReplay(true);
        const data = await getDecisionReplay(selectedOrderId!);
        setReplayData(data);
      } catch (err) {
        console.error("Failed to load decision replay:", err);
      } finally {
        setLoadingReplay(false);
      }
    }
    loadReplay();
  }, [selectedOrderId]);

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <div className="flex items-center gap-2">
          <History size={24} className="text-blue-400" />
          <h1 className="page-title text-2xl font-bold text-white">Decision Replay & Audit Reconstruction</h1>
        </div>
        <p className="page-subtitle text-slate-400 text-sm mt-1">
          Full cryptographic and structural playback of the AI governance pipeline from user intent to payment webhook.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Orders Selection Panel */}
        <div className="card h-fit">
          <div className="text-sm font-bold text-white mb-3 flex items-center justify-between">
            <span>Transactions ({orders.length})</span>
            <span className="text-xs text-slate-400">Select to Replay</span>
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {orders.map((o) => {
              const isSelected = o.id === selectedOrderId;
              return (
                <button
                  key={o.id}
                  onClick={() => setSelectedOrderId(o.id)}
                  className={`w-full text-left p-3 rounded-xl border transition-all text-xs ${
                    isSelected
                      ? "bg-blue-600/15 border-blue-500 text-white"
                      : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                  }`}
                >
                  <div className="flex justify-between items-center mb-1 font-mono">
                    <span className="font-bold text-blue-300">{o.id}</span>
                    <span className="font-bold text-white">₹{o.amount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400 text-[11px]">
                    <span className="capitalize">{o.order_type.replace("_", " ")}</span>
                    <span className={`badge text-[10px] px-2 py-0.5 rounded-full ${
                      o.payment_status === "captured" ? "text-emerald-400 bg-emerald-500/10" : "text-amber-400 bg-amber-500/10"
                    }`}>
                      {o.payment_status}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* 12-Stage Decision Replay Visualizer */}
        <div className="lg:col-span-2 space-y-4">
          {loadingReplay ? (
            <div className="card text-center py-20">
              <History size={32} className="animate-spin text-blue-400 mx-auto mb-3" />
              <p className="text-slate-400">Reconstructing Governance Journey...</p>
            </div>
          ) : replayData ? (
            <>
              {/* Summary Card */}
              <div className="card p-5 bg-gradient-to-r from-slate-900 to-slate-950 border border-slate-800 flex justify-between items-center flex-wrap gap-4">
                <div>
                  <div className="text-xs text-slate-500 font-mono">REPLAY TRANSACTION</div>
                  <div className="text-xl font-bold text-white mt-0.5">{replayData.order_id}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    Amount: <strong className="text-white">₹{replayData.amount.toLocaleString()} {replayData.currency}</strong> | Status: <span className="text-emerald-400 font-semibold">{replayData.status}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="badge badge-success px-3 py-1 text-xs rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold">
                    100% Verified Trace
                  </span>
                </div>
              </div>

              {/* Stages Timeline */}
              <div className="card space-y-4">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Clock size={16} className="text-blue-400" />
                  Deterministic Execution Journey
                </h3>

                <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                  {replayData.stages.map((stage, idx) => (
                    <div key={idx} className="relative">
                      <div className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-blue-600 border-2 border-slate-950 flex items-center justify-center text-[9px] text-white font-bold">
                        {idx + 1}
                      </div>

                      <div className="bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
                        <div className="flex justify-between items-center gap-2 mb-1">
                          <span className="text-xs font-bold text-blue-300 font-mono">{stage.title}</span>
                          <span className="text-[10px] text-slate-500">{stage.timestamp}</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{stage.summary}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Underlying Audit Logs */}
              <div className="card">
                <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                  <Shield size={16} className="text-emerald-400" />
                  Linked Immutable Audit Logs ({replayData.audit_logs.length})
                </h3>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {replayData.audit_logs.map((log) => (
                    <div key={log.id} className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800 text-xs font-mono flex justify-between items-center text-slate-300">
                      <div>
                        <span className="text-blue-400 font-bold">{log.action}</span> by <span className="text-slate-400">{log.actor}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-emerald-400">{log.result}</span>
                        <span className="text-[10px] text-slate-500">{log.timestamp.slice(11, 19)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="card text-center py-20 text-slate-500">No transaction selected</div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
