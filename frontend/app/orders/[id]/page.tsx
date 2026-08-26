"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AppLayout from "@/components/AppLayout";
import {
  ClipboardList,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Clock,
  Shield,
  CreditCard,
  Radio,
  FileText,
  RotateCcw,
  Sparkles,
} from "lucide-react";
import { getOrder, getDecisionReplay } from "@/services/api";
import { Order, DecisionReplayData } from "@/types";

export default function OrderDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params?.id as string;

  const [order, setOrder] = useState<Order | null>(null);
  const [decisionReplay, setDecisionReplay] = useState<DecisionReplayData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReplay, setShowReplay] = useState(false);

  useEffect(() => {
    if (!orderId) return;

    Promise.all([
      getOrder(orderId).catch(() => null),
      getDecisionReplay(orderId).catch(() => null),
    ])
      .then(([ord, replay]) => {
        setOrder(ord);
        setDecisionReplay(replay);
      })
      .finally(() => setLoading(false));
  }, [orderId]);

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="spinner w-8 h-8 text-blue-500" />
        </div>
      </AppLayout>
    );
  }

  if (!order) {
    return (
      <AppLayout>
        <div className="card text-center p-12">
          <AlertCircle className="mx-auto text-rose-400 mb-3" size={36} />
          <h2 className="text-lg font-bold text-gray-200">Order Not Found</h2>
          <p className="text-sm text-gray-400 mt-1 mb-4">The requested order ID does not exist in the database.</p>
          <button onClick={() => router.push("/orders")} className="btn btn-secondary btn-sm mx-auto">
            ← Back to Orders
          </button>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => router.push("/orders")}
            className="text-xs text-gray-400 hover:text-white flex items-center gap-1 mb-2"
          >
            <ArrowLeft size={12} />
            <span>Back to Orders</span>
          </button>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ClipboardList className="text-indigo-400" />
            Order #{order.id}
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">
            Placed on {new Date(order.created_at).toLocaleString()} • Type: <span className="font-semibold text-indigo-300">{order.order_type}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowReplay(!showReplay)}
            className="btn btn-secondary flex items-center gap-1.5 text-sm"
          >
            <Sparkles size={14} className="text-amber-400" />
            <span>{showReplay ? "Hide Decision Replay" : "View Decision Replay"}</span>
          </button>
        </div>
      </div>

      {/* Decision Replay Modal/Banner */}
      {showReplay && decisionReplay && (
        <div className="card bg-indigo-950/30 border border-indigo-500/40 mb-8 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-indigo-900/50 pb-3 mb-4">
            <h2 className="text-base font-bold text-indigo-200 flex items-center gap-2">
              <RotateCcw size={16} className="text-indigo-400" />
              Decision Replay: Full Autonomous Journey Reconstruction
            </h2>
            <span className="badge badge-info text-xs font-mono">100% Data-Backed</span>
          </div>

          <p className="text-xs text-gray-300 mb-6">
            Reconstructed from persistent trace logs and immutable audit records for this exact transaction:
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {decisionReplay.stages.map((st) => (
              <div key={st.sequence} className="p-3 rounded-lg bg-black/40 border border-indigo-900/60 space-y-1">
                <div className="flex items-center justify-between text-xs font-mono font-bold text-indigo-300">
                  <span>{st.title}</span>
                  <span className="text-emerald-400">{st.status}</span>
                </div>
                <p className="text-xs text-gray-300">{st.summary}</p>
                <span className="text-[10px] text-gray-500 block font-mono">
                  {new Date(st.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>

          {/* Decision Factors */}
          {decisionReplay.decision_factors && decisionReplay.decision_factors.factors && (
            <div className="p-4 rounded-lg bg-black/50 border border-indigo-900/50 space-y-2">
              <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                Governance & Decision Factors
              </h4>
              <ul className="text-xs space-y-1 text-gray-300">
                {decisionReplay.decision_factors.factors.map((f, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-emerald-400">✓</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Order Summary & Financial Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
            Order Total
          </span>
          <p className="text-2xl font-bold text-white">₹{order.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</p>
          <span className="text-xs text-gray-400 mt-1 block">Currency: {order.currency}</span>
        </div>

        <div className="card">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
            Payment State
          </span>
          <div className="flex items-center gap-2 mt-1">
            <span
              className={`badge uppercase font-bold text-xs ${
                order.payment_status === "captured"
                  ? "badge-success"
                  : order.payment_status === "failed"
                  ? "badge-danger"
                  : "badge-warning"
              }`}
            >
              {order.payment_status}
            </span>
          </div>
          <span className="text-xs text-gray-400 mt-2 block font-mono">
            Razorpay Order: {order.razorpay_order_id || "N/A"}
          </span>
        </div>

        <div className="card">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
            State Machine Status
          </span>
          <div className="flex items-center gap-2 mt-1">
            <span className="badge badge-info uppercase font-bold text-xs">
              {order.status}
            </span>
          </div>
          <span className="text-xs text-gray-400 mt-2 block font-mono">
            Receipt: {order.receipt || "N/A"}
          </span>
        </div>
      </div>

      {/* Order Timeline */}
      <div className="card">
        <h2 className="text-base font-bold text-gray-200 mb-6 flex items-center gap-2">
          <Clock size={16} className="text-indigo-400" />
          Step-by-Step Order Timeline
        </h2>

        {order.timeline && order.timeline.length > 0 ? (
          <div className="relative border-l border-gray-800 ml-4 space-y-6 pb-2">
            {order.timeline.map((event, idx) => (
              <div key={idx} className="relative pl-6">
                <div className="absolute -left-1.5 top-1 w-3 h-3 rounded-full bg-indigo-500 border-2 border-gray-900" />
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <h4 className="text-sm font-semibold text-gray-200">{event.step.replace(/_/g, " ")}</h4>
                  <span className="text-xs text-gray-500 font-mono">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-indigo-400 font-mono">Actor: {event.actor}</span>
                  <span className="text-xs text-gray-400">• Status: {event.status}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-500">No timeline events recorded.</p>
        )}
      </div>
    </AppLayout>
  );
}
