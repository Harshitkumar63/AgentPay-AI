"use client";

import { useState } from "react";
import Link from "next/link";
import AppLayout from "@/components/AppLayout";
import {
  Code,
  Key,
  Copy,
  Check,
  Zap,
  Terminal,
  ExternalLink,
  Shield,
  Layers,
  Play,
} from "lucide-react";

export default function DeveloperPortalPage() {
  const [copiedKey, setCopiedKey] = useState(false);
  const [apiKey, setApiKey] = useState("agp_live_8f7b32c19a4e67290d");
  const [showKeyModal, setShowKeyModal] = useState(false);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const generateNewKey = () => {
    const newK = `agp_live_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 10)}`;
    setApiKey(newK);
    setShowKeyModal(true);
  };

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <div className="flex justify-between items-center flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Code size={24} className="text-blue-400" />
              <h1 className="page-title text-2xl font-bold text-white">Developer Portal & Machine APIs</h1>
            </div>
            <p className="page-subtitle text-slate-400 text-sm mt-1">
              Connect external AI agents, autonomous buyers, and MCP servers directly to the AgentPay Commerce Engine.
            </p>
          </div>
          <Link href="/developers/playground" className="btn btn-primary flex items-center gap-2">
            <Play size={16} />
            Open API Playground
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: API Keys & Credentials */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <Key size={16} className="text-amber-400" />
              Machine-to-Machine API Keys
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Use API keys in the <code>X-Agent-Key</code> header or Bearer authorization for AI Buyer API requests.
            </p>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between mb-4">
              <span className="font-mono text-xs text-slate-300 truncate mr-2">
                {apiKey.substring(0, 12)}••••••••••••
              </span>
              <button
                onClick={() => copyToClipboard(apiKey)}
                className="btn btn-secondary text-xs py-1 px-2.5 flex items-center gap-1 shrink-0"
              >
                {copiedKey ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                {copiedKey ? "Copied" : "Copy"}
              </button>
            </div>

            <button onClick={generateNewKey} className="btn btn-secondary w-full text-xs py-2">
              Generate New API Key
            </button>
          </div>

          <div className="card">
            <h3 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
              <Shield size={16} className="text-emerald-400" />
              Available Scopes
            </h3>
            <div className="space-y-2 text-xs font-mono">
              {[
                { scope: "catalog:read", desc: "Read structured product catalog and inventory" },
                { scope: "cart:write", desc: "Create carts and manage shopping items" },
                { scope: "checkout:create", desc: "Submit orders into policy approval gate" },
                { scope: "payment:read", desc: "Read verified payment capture status" },
              ].map((s) => (
                <div key={s.scope} className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                  <div className="text-blue-400 font-bold">{s.scope}</div>
                  <div className="text-[11px] text-slate-400 font-sans mt-0.5">{s.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Code Quickstart & Endpoints */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-base font-bold text-white mb-2 flex items-center gap-2">
              <Terminal size={18} className="text-blue-400" />
              Autonomous Agent Quickstart (Python)
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              External agents can discover catalog items, build carts, and trigger policy-gated checkouts via standard HTTP.
            </p>

            <pre className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto leading-relaxed">
{`import requests

AGENT_KEY = "${apiKey}"
BASE_URL = "http://localhost:8000/api/agent/v1"
HEADERS = {"X-Agent-Key": AGENT_KEY}

# 1. Search products
search_res = requests.post(
    f"{BASE_URL}/search",
    json={"query": "running shoes", "max_price": 3000.0},
    headers=HEADERS
).json()

selected_product = search_res["results"][0]

# 2. Create Cart & Add Item
cart = requests.post(f"{BASE_URL}/cart", headers=HEADERS).json()
requests.post(
    f"{BASE_URL}/cart/{cart['id']}/items",
    json={"product_id": selected_product["id"], "quantity": 1},
    headers=HEADERS
)

# 3. Gated Checkout Pipeline
checkout = requests.post(
    f"{BASE_URL}/checkout",
    json={"cart_id": cart["id"], "idempotency_key": "order_idem_1234"},
    headers=HEADERS
).json()

print(f"Order Status: {checkout['status']} (Requires Human Approval: {checkout['requires_approval']})")`}
            </pre>
          </div>

          <div className="card">
            <h3 className="text-sm font-bold text-white mb-3">AI Buyer API (v1) Reference Endpoints</h3>
            <div className="space-y-2 text-xs font-mono">
              {[
                { method: "GET", path: "/api/agent/v1/tools", desc: "Retrieve OpenAI / MCP Tool Calling schema definitions" },
                { method: "GET", path: "/api/agent/v1/catalog", desc: "Fetch AI-optimized catalog with factual stock and specs" },
                { method: "POST", path: "/api/agent/v1/search", desc: "Natural language & price-filtered product discovery" },
                { method: "POST", path: "/api/agent/v1/cart", desc: "Create an agent shopping cart session" },
                { method: "POST", path: "/api/agent/v1/checkout", desc: "Execute full price recomputation, policy check & approval gate" },
                { method: "GET", path: "/api/agent/v1/orders/{id}", desc: "Check verified order state & delivery timeline" },
              ].map((ep, i) => (
                <div key={i} className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      ep.method === "POST" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    }`}>
                      {ep.method}
                    </span>
                    <span className="text-white font-semibold">{ep.path}</span>
                  </div>
                  <span className="text-slate-400 text-[11px] font-sans text-right hidden sm:inline">{ep.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
