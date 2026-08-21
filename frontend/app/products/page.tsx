"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Package, Tag, DollarSign } from "lucide-react";
import { getProducts } from "@/services/api";
import type { Product } from "@/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProducts("merchant_001")
      .then(setProducts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div className="page-header">
        <h1><Package size={28} style={{ display: "inline", marginRight: 10, verticalAlign: "middle" }} />Products</h1>
        <p>Manage your product catalog • {products.length} products</p>
      </div>

      {loading ? (
        <div className="loading"><div className="spinner" /></div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Status</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{p.name}</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{p.id}</div>
                  </td>
                  <td><span className="badge badge-purple">{p.category}</span></td>
                  <td style={{ fontWeight: 600 }}>₹{p.price.toLocaleString("en-IN")}</td>
                  <td>{p.stock}</td>
                  <td>
                    <span className={`badge ${p.active && p.stock > 0 ? "badge-success" : "badge-danger"}`}>
                      {p.active && p.stock > 0 ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                      {(p.tags || []).slice(0, 3).map((t) => (
                        <span key={t} className="product-tag">{t}</span>
                      ))}
                    </div>
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
