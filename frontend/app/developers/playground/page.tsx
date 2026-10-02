"use client";

import { useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import {
  Play,
  ArrowLeft,
  Clock,
  CheckCircle2,
  Code,
  Send,
  RefreshCw,
} from "lucide-react";
import {
  getBuyerTools,
  getCatalog,
  buyerSearch,
  buyerCreateCart,
  buyerCheckout,
  getMcpTools,
} from "@/services/api";

export default function DeveloperPlaygroundPage() {
  const [selectedEndpoint, setSelectedEndpoint] = useState("search");
  const [requestBody, setRequestBody] = useState(
    JSON.stringify({ query: "running shoes", max_price: 3000 }, null, 2)
  );
  const [response, setResponse] = useState<any>(null);
  const [status, setStatus] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  const endpoints = [
    {
      id: "tools",
      name: "GET /api/agent/v1/tools",
      method: "GET",
      defaultBody: "",
      runner: async () => await getBuyerTools(),
    },
    {
      id: "catalog",
      name: "GET /api/agent/v1/catalog",
      method: "GET",
      defaultBody: "",
      runner: async () => await getCatalog(),
    },
    {
      id: "search",
      name: "POST /api/agent/v1/search",
      method: "POST",
      defaultBody: JSON.stringify({ query: "running shoes", max_price: 3000 }, null, 2),
      runner: async (body: any) => await buyerSearch(body.query || "shoes", body.max_price),
    },
    {
      id: "cart",
      name: "POST /api/agent/v1/cart",
      method: "POST",
      defaultBody: JSON.stringify({ user_id: "ai_buyer_agent" }, null, 2),
      runner: async () => await buyerCreateCart(),
    },
    {
      id: "checkout",
      name: "POST /api/agent/v1/checkout",
      method: "POST",
      defaultBody: JSON.stringify(
        {
          cart_id: "cart_seed_0",
          user_id: "ai_buyer_agent",
          idempotency_key: `idem_${Date.now()}`,
        },
        null,
        2
      ),
      runner: async (body: any) => await buyerCheckout(body.cart_id, body.idempotency_key),
    },
    {
      id: "mcp",
      name: "GET /api/mcp/tools",
      method: "GET",
      defaultBody: "",
      runner: async () => await getMcpTools(),
    },
  ];

  const handleSelectEndpoint = (epId: string) => {
    setSelectedEndpoint(epId);
    const ep = endpoints.find((e) => e.id === epId);
    if (ep) {
      setRequestBody(ep.defaultBody);
      setResponse(null);
      setStatus(null);
      setLatency(null);
    }
  };

  const executeRequest = async () => {
    const ep = endpoints.find((e) => e.id === selectedEndpoint);
    if (!ep) return;

    try {
      setLoading(true);
      const start = performance.now();
      let parsedBody = {};
      if (ep.method === "POST" && requestBody) {
        parsedBody = JSON.parse(requestBody);
      }
      const data = await ep.runner(parsedBody);
      const end = performance.now();

      setResponse(data);
      setStatus(200);
      setLatency(Math.round(end - start));
    } catch (err: any) {
      setResponse({ error: err.message });
      setStatus(400);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <Link href="/developers" className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white mb-3">
          <ArrowLeft size={14} /> Back to Developer Portal
        </Link>
        <div className="flex items-center gap-2">
          <Play size={24} className="text-blue-400" />
          <h1 className="page-title text-2xl font-bold text-white">Interactive API Playground</h1>
        </div>
        <p className="page-subtitle text-slate-400 text-sm mt-1">
          Test AI Buyer endpoints, tool specifications, and checkout governance in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Endpoints Sidebar */}
        <div className="lg:col-span-4 space-y-2">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Select Endpoint</div>
          {endpoints.map((ep) => {
            const isSelected = ep.id === selectedEndpoint;
            return (
              <button
                key={ep.id}
                onClick={() => handleSelectEndpoint(ep.id)}
                className={`w-full text-left p-3 rounded-xl border text-xs font-mono transition-all flex items-center justify-between ${
                  isSelected
                    ? "bg-blue-600/15 border-blue-500 text-white"
                    : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                    ep.method === "POST" ? "bg-emerald-500/10 text-emerald-400" : "bg-blue-500/10 text-blue-400"
                  }`}>
                    {ep.method}
                  </span>
                  <span>{ep.name.replace(/^GET |^POST /, "")}</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Request & Response Workspace */}
        <div className="lg:col-span-8 space-y-4">
          {/* Request Header Bar */}
          <div className="card p-4 flex justify-between items-center flex-wrap gap-3">
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="text-emerald-400 font-bold">
                {endpoints.find((e) => e.id === selectedEndpoint)?.method}
              </span>
              <span className="text-white">
                {endpoints.find((e) => e.id === selectedEndpoint)?.name.replace(/^GET |^POST /, "")}
              </span>
            </div>

            <button
              onClick={executeRequest}
              disabled={loading}
              className="btn btn-primary text-xs py-2 px-4 flex items-center gap-2"
            >
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
              Send Request
            </button>
          </div>

          {/* Request Body (if POST) */}
          {endpoints.find((e) => e.id === selectedEndpoint)?.method === "POST" && (
            <div className="card">
              <div className="text-xs font-bold text-slate-400 mb-2">Request Body (JSON)</div>
              <textarea
                value={requestBody}
                onChange={(e) => setRequestBody(e.target.value)}
                rows={5}
                className="w-full bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono text-slate-200 focus:border-blue-500 focus:outline-none"
              />
            </div>
          )}

          {/* Response Pane */}
          <div className="card">
            <div className="flex justify-between items-center mb-3">
              <div className="text-xs font-bold text-slate-300">Live Response</div>
              {status && (
                <div className="flex items-center gap-3 text-xs font-mono">
                  <span className={`px-2 py-0.5 rounded ${status === 200 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}`}>
                    Status: {status} OK
                  </span>
                  {latency && (
                    <span className="text-slate-400 flex items-center gap-1">
                      <Clock size={12} /> {latency}ms
                    </span>
                  )}
                </div>
              )}
            </div>

            <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto max-h-[450px]">
              {response ? JSON.stringify(response, null, 2) : "// Click 'Send Request' to execute endpoint against live backend."}
            </pre>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
