"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Headphones,
  Send,
  CheckCircle2,
  Package,
  CreditCard,
  RotateCcw,
  ShieldCheck,
  Info,
  Sparkles,
} from "lucide-react";
import { querySupportAgent, createRefundRequest } from "@/services/api";
import { SupportResponse } from "@/types";

export default function CustomerSupportPage() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; text: string; data?: SupportResponse }[]>([
    {
      role: "assistant",
      text: "Hello! I am UrbanCart's AI Support Agent. I have verified access to real-time order states, payment capture records, and refund requests. How can I assist you today?",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const quickQuestions = [
    "Where is my order?",
    "Has my payment succeeded?",
    "Can I cancel my order?",
    "What is my refund status?",
  ];

  const handleSend = async (userQuery: string) => {
    const q = userQuery || query;
    if (!q.trim()) return;

    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await querySupportAgent(q, "demo_user");
      setMessages((prev) => [...prev, { role: "assistant", text: res.answer, data: res }]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message || "Failed to reach support service."}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestRefund = async (orderId: string, amount: number) => {
    try {
      await createRefundRequest({
        order_id: orderId,
        amount: amount,
        reason: "Customer support initiated refund request",
      });
      alert(`Refund request for Order ${orderId} submitted successfully into the approval queue.`);
      handleSend("What is my refund status?");
    } catch (err: any) {
      alert(err.message || "Failed to request refund");
    }
  };

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <div className="flex items-center gap-2">
          <Headphones size={24} className="text-blue-400" />
          <h1 className="page-title text-2xl font-bold text-white">Customer Support Agent</h1>
        </div>
        <p className="page-subtitle text-slate-400 text-sm mt-1">
          Zero-hallucination customer support grounded strictly in verified database orders, payments, and refund records.
        </p>
      </div>

      {/* Trust Guarantee Banner */}
      <div className="card p-3.5 mb-6 bg-blue-950/20 border border-blue-500/30 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2.5 text-xs text-blue-300">
          <ShieldCheck size={18} className="text-blue-400 shrink-0" />
          <span>
            <strong>Anti-Hallucination Grounding Active:</strong> Answers query authoritative PostgreSQL / SQLite order records.
          </span>
        </div>
        <span className="badge text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
          100% FACTUAL
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Chat Stream */}
        <div className="lg:col-span-8 space-y-4">
          <div className="card p-4 min-h-[480px] max-h-[580px] flex flex-col justify-between overflow-hidden">
            {/* Messages */}
            <div className="space-y-4 overflow-y-auto pr-1 flex-1 mb-4">
              {messages.map((m, idx) => (
                <div
                  key={idx}
                  className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                      m.role === "user"
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none"
                    }`}
                  >
                    <div className="whitespace-pre-line">{m.text}</div>

                    {/* Grounded Details Card if present */}
                    {m.data?.order_details && (
                      <div className="mt-3 p-3 bg-slate-900/90 rounded-xl border border-slate-800 text-[11px] space-y-1">
                        <div className="font-bold text-white flex items-center justify-between">
                          <span>Order #{m.data.order_details.order_id}</span>
                          <span className="text-blue-400">₹{m.data.order_details.amount.toLocaleString()}</span>
                        </div>
                        <div className="text-slate-400">
                          Status: <strong className="text-emerald-400">{m.data.order_details.status}</strong> | Payment: {m.data.order_details.payment_status}
                        </div>
                        {m.data.payment_details && (
                          <div className="text-slate-400 font-mono text-[10px]">
                            Razorpay ID: {m.data.payment_details.razorpay_payment_id || "Pending"}
                          </div>
                        )}
                        {m.data.order_details.payment_status === "captured" && (
                          <button
                            onClick={() => handleRequestRefund(m.data!.order_details!.order_id, m.data!.order_details!.amount)}
                            className="btn btn-secondary text-[10px] py-1 px-2.5 mt-2 text-red-400 hover:bg-red-500/10 flex items-center gap-1"
                          >
                            <RotateCcw size={11} /> Request Refund for this Order
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex items-center gap-2 text-xs text-slate-400 italic">
                  <Sparkles size={14} className="animate-spin text-blue-400" />
                  Querying database records...
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="space-y-2">
              {/* Quick Prompts */}
              <div className="flex flex-wrap gap-1.5">
                {quickQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="text-[11px] px-2.5 py-1 rounded-full bg-slate-950 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
                  >
                    {q}
                  </button>
                ))}
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend(query);
                }}
                className="flex gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask about order tracking, payments, refunds..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="flex-1 bg-slate-950 px-4 py-2.5 rounded-xl border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={loading || !query.trim()}
                  className="btn btn-primary px-4 py-2.5 text-xs flex items-center gap-2"
                >
                  <Send size={14} /> Send
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Sidebar: Capabilities */}
        <div className="lg:col-span-4 space-y-4">
          <div className="card space-y-3">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Grounding Guarantees</h3>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-start gap-2">
                <Package size={16} className="text-blue-400 shrink-0 mt-0.5" />
                <span><strong>Real Order States:</strong> Syncs with backend order lifecycle and delivery timeline.</span>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-start gap-2">
                <CreditCard size={16} className="text-emerald-400 shrink-0 mt-0.5" />
                <span><strong>Cryptographic Payment Checks:</strong> References HMAC-verified Razorpay payments.</span>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex items-start gap-2">
                <RotateCcw size={16} className="text-purple-400 shrink-0 mt-0.5" />
                <span><strong>Gated Refund Lifecycle:</strong> Routes customer cancellations into human approval workflows.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
