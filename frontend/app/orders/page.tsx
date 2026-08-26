"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import { ClipboardList, ArrowRight, RotateCcw } from "lucide-react";
import { getOrders } from "@/services/api";
import type { Order } from "@/types";

const statusColors: Record<string, string> = {
  ORDER_CREATED: "badge-info",
  APPROVAL_PENDING: "badge-warning",
  APPROVED: "badge-info",
  PAYMENT_PENDING: "badge-warning",
  PAYMENT_AUTHORIZED: "badge-info",
  PAYMENT_CAPTURED: "badge-success",
  COMPLETED: "badge-success",
  confirmed: "badge-success",
  created: "badge-info",
  PAYMENT_FAILED: "badge-danger",
  failed: "badge-danger",
  CANCELLED: "badge-danger",
  EXPIRED: "badge-danger",
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getOrders("merchant_001")
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="page-header">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <ClipboardList className="text-indigo-400" />
          Orders, Timelines & Decision Replay
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Complete state machine ledger of store orders • {orders.length} total orders recorded
        </p>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner" />
        </div>
      ) : orders.length === 0 ? (
        <div className="empty-state">
          <ClipboardList size={48} className="mx-auto mb-2 opacity-50 text-indigo-400" />
          <h3 className="text-base font-bold text-gray-200">No Orders Yet</h3>
          <p className="text-xs text-gray-400 mt-1">
            Orders will appear here after customers or external AI agents make purchases via AI Shop or AI Buyer API.
          </p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Amount</th>
                <th>State Machine Status</th>
                <th>Payment</th>
                <th>Type</th>
                <th>Razorpay ID</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="hover:bg-gray-900/50 transition-colors">
                  <td className="font-mono font-semibold text-indigo-300">{o.id}</td>
                  <td className="font-bold">₹{o.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
                  <td>
                    <span className={`badge uppercase font-bold text-[10px] ${statusColors[o.status] || "badge-info"}`}>
                      {o.status}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge uppercase font-bold text-[10px] ${
                        o.payment_status === "captured"
                          ? "badge-success"
                          : o.payment_status === "failed"
                          ? "badge-danger"
                          : "badge-warning"
                      }`}
                    >
                      {o.payment_status}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-purple text-[10px] font-mono">
                      {o.order_type.replace("_", " ")}
                    </span>
                  </td>
                  <td className="font-mono text-xs text-gray-400">{o.razorpay_order_id || "—"}</td>
                  <td className="text-xs text-gray-400">{new Date(o.created_at).toLocaleString()}</td>
                  <td>
                    <Link
                      href={`/orders/${o.id}`}
                      className="btn btn-secondary btn-sm text-xs py-1 px-2 flex items-center gap-1 w-fit"
                    >
                      <RotateCcw size={11} className="text-indigo-400" />
                      <span>Timeline & Replay</span>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}
