"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { BarChart3, TrendingUp, DollarSign, ShoppingCart, Bot } from "lucide-react";
import { getRevenueAnalytics, getProductAnalytics } from "@/services/api";
import type { RevenueAnalytics } from "@/types";

interface ProductAnalytic {
  product_id: string;
  product_name: string;
  category: string;
  price: number;
  stock: number;
  total_sold: number;
  total_revenue: number;
}

export default function AnalyticsPage() {
  const [revenue, setRevenue] = useState<RevenueAnalytics | null>(null);
  const [products, setProducts] = useState<ProductAnalytic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getRevenueAnalytics().catch(() => null),
      getProductAnalytics().catch(() => []),
    ]).then(([rev, prod]) => {
      setRevenue(rev);
      setProducts(prod as ProductAnalytic[]);
    }).finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="page-header">
        <h1><BarChart3 size={28} style={{ display: "inline", marginRight: 10, verticalAlign: "middle" }} />Analytics</h1>
        <p>Revenue insights, product performance, and AI-assisted metrics</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : (
        <>
          {/* Revenue Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-card-header">
                <span className="stat-card-label">Total Revenue</span>
                <div className="stat-card-icon" style={{ background: "rgba(0,184,148,0.1)" }}>
                  <DollarSign size={18} style={{ color: "#00b894" }} />
                </div>
              </div>
              <div className="stat-card-value">₹{(revenue?.total_revenue ?? 0).toLocaleString("en-IN")}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-header">
                <span className="stat-card-label">AI Revenue</span>
                <div className="stat-card-icon" style={{ background: "rgba(108,92,231,0.15)" }}>
                  <Bot size={18} style={{ color: "#6c5ce7" }} />
                </div>
              </div>
              <div className="stat-card-value">₹{(revenue?.ai_assisted_revenue ?? 0).toLocaleString("en-IN")}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-header">
                <span className="stat-card-label">Upsell Revenue</span>
                <div className="stat-card-icon" style={{ background: "rgba(162,155,254,0.1)" }}>
                  <TrendingUp size={18} style={{ color: "#a29bfe" }} />
                </div>
              </div>
              <div className="stat-card-value">₹{(revenue?.upsell_revenue ?? 0).toLocaleString("en-IN")}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-header">
                <span className="stat-card-label">Cross-sell Revenue</span>
                <div className="stat-card-icon" style={{ background: "rgba(116,185,255,0.1)" }}>
                  <ShoppingCart size={18} style={{ color: "#74b9ff" }} />
                </div>
              </div>
              <div className="stat-card-value">₹{(revenue?.cross_sell_revenue ?? 0).toLocaleString("en-IN")}</div>
            </div>
          </div>

          {/* Product Performance */}
          <div style={{ marginTop: 32 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>Product Performance</h2>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Stock</th>
                    <th>Units Sold</th>
                    <th>Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((p) => (
                    <tr key={p.product_id}>
                      <td style={{ fontWeight: 600, color: "var(--text-primary)" }}>{p.product_name}</td>
                      <td><span className="badge badge-purple">{p.category}</span></td>
                      <td>₹{p.price.toLocaleString("en-IN")}</td>
                      <td>{p.stock}</td>
                      <td>{p.total_sold}</td>
                      <td style={{ fontWeight: 600, color: "var(--success)" }}>₹{p.total_revenue.toLocaleString("en-IN")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Note about demo data */}
          <div style={{ marginTop: 24, padding: 16, background: "var(--warning-bg)", borderRadius: "var(--radius-sm)", fontSize: 13, color: "var(--warning)" }}>
            📊 Analytics data is based on actual orders processed through the system. Complete a purchase via the AI Shop to see metrics update.
          </div>
        </>
      )}
    </AppLayout>
  );
}
