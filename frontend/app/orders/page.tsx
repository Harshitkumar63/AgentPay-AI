"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { ClipboardList } from "lucide-react";
import { getOrders } from "@/services/api";
import type { Order } from "@/types";

const statusColors: Record<string, string> = {
  created: "badge-info",
  confirmed: "badge-success",
  fulfilled: "badge-success",
  cancelled: "badge-danger",
  pending: "badge-warning",
  authorized: "badge-info",
  captured: "badge-success",
  failed: "badge-danger",
  refunded: "badge-warning",
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
        <h1><ClipboardList size={28} style={{ display: "inline", marginRight: 10, verticalAlign: "middle" }} />Orders</h1>
        <p>Track all orders and payment statuses • {orders.length} orders</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : orders.length === 0 ? (
        <div className="empty-state">
          <ClipboardList size={48} />
          <h3>No orders yet</h3>
          <p>Orders will appear here after customers make purchases via the AI Shop.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Payment</th>
                <th>Type</th>
                <th>Razorpay ID</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{o.id}</td>
                  <td style={{ fontWeight: 600 }}>₹{o.amount.toLocaleString("en-IN")}</td>
                  <td><span className={`badge ${statusColors[o.status] || "badge-info"}`}>{o.status}</span></td>
                  <td><span className={`badge ${statusColors[o.payment_status] || "badge-warning"}`}>{o.payment_status}</span></td>
                  <td><span className="badge badge-purple">{o.order_type.replace("_", " ")}</span></td>
                  <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{o.razorpay_order_id || "—"}</td>
                  <td style={{ fontSize: 13 }}>{new Date(o.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}
