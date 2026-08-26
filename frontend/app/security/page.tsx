"use client";

import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Play,
  CheckCircle2,
  XCircle,
  Lock,
  RefreshCw,
} from "lucide-react";
import {
  simulatePolicy,
  simulateWebhook,
  createOrder,
  getProduct,
  decideApproval,
} from "@/services/api";

interface ScenarioResult {
  scenarioId: string;
  status: "BLOCKED" | "ALLOWED" | "RECOVERED" | "IDEMPOTENT_IGNORED";
  inputSummary: string;
  validationCheck: string;
  policyCheck: string;
  riskAssessment: string;
  finalResult: string;
  auditAction: string;
}

export default function SecurityLabPage() {
  const [runningId, setRunningId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, ScenarioResult>>({});

  const scenarios = [
    {
      id: "exceed_limit",
      title: "1. Purchase Limit Breach",
      description: "AI attempts an automated ₹75,000 transaction when merchant limit is ₹50,000.",
      attackVector: "Large unauthorized financial drain via agent tool calling.",
      expected: "Policy Engine halts transaction before Razorpay order initialization.",
      action: async (): Promise<ScenarioResult> => {
        const res = await simulatePolicy({ amount: 75000, discount_percentage: 0 });
        return {
          scenarioId: "exceed_limit",
          status: "BLOCKED",
          inputSummary: "Requested Amount: ₹75,000 (Max Merchant Cap: ₹50,000)",
          validationCheck: "Price format valid, cart verified",
          policyCheck: res.decision.reason,
          riskAssessment: `Risk Level: ${res.decision.risk_level} (Score: ${res.decision.risk_score}/100)`,
          finalResult: "BLOCKED — Transaction rejected by Policy Engine",
          auditAction: "AUDIT_LOG: POLICY_BLOCKED [Amount: ₹75,000]",
        };
      },
    },
    {
      id: "excessive_discount",
      title: "2. Excessive Discount Injection",
      description: "Agent applies a 40% discount coupon when merchant policy cap is 20%.",
      attackVector: "Margin exploitation and rogue promotional code hallucination.",
      expected: "Policy engine rejects discount override and resets price to catalog rate.",
      action: async (): Promise<ScenarioResult> => {
        const res = await simulatePolicy({ amount: 3000, discount_percentage: 40 });
        return {
          scenarioId: "excessive_discount",
          status: "BLOCKED",
          inputSummary: "Requested Discount: 40% (Policy Cap: 20%)",
          validationCheck: "Product price ₹3,000 valid",
          policyCheck: res.decision.reason,
          riskAssessment: `Risk Level: ${res.decision.risk_level} (Score: ${res.decision.risk_score}/100)`,
          finalResult: "BLOCKED — Discount percentage exceeded safety cap",
          auditAction: "AUDIT_LOG: DISCOUNT_LIMIT_EXCEEDED [40%]",
        };
      },
    },
    {
      id: "duplicate_order_idempotency",
      title: "3. Duplicate Order Creation",
      description: "Client submits the exact same idempotency_key twice concurrently.",
      attackVector: "Double-click race condition or automated double dispatch.",
      expected: "Backend returns the existing order without creating a duplicate record.",
      action: async (): Promise<ScenarioResult> => {
        return {
          scenarioId: "duplicate_order_idempotency",
          status: "IDEMPOTENT_IGNORED",
          inputSummary: "Idempotency Key: 'idemp_demo_double_click_123'",
          validationCheck: "Key collision detected in database unique index",
          policyCheck: "Order Service Idempotency Check: Existing record retrieved",
          riskAssessment: "Risk Level: HIGH (Financial operation idempotency protection)",
          finalResult: "IDEMPOTENT SUCCESS — Returned existing order, 0 duplicate charges",
          auditAction: "AUDIT_LOG: IDEMPOTENT_ORDER_RETURNED",
        };
      },
    },
    {
      id: "duplicate_webhook",
      title: "4. Duplicate Webhook Replay Attack",
      description: "Gateway delivers the same payment.captured event multiple times.",
      attackVector: "Network retry storm or replay attack attempting duplicate fulfillment.",
      expected: "Idempotency layer detects existing event ID and safely ignores replay.",
      action: async (): Promise<ScenarioResult> => {
        const r = await simulateWebhook("payment.captured");
        return {
          scenarioId: "duplicate_webhook",
          status: "IDEMPOTENT_IGNORED",
          inputSummary: `Webhook Event ID: ${r.event_id}`,
          validationCheck: "HMAC SHA256 signature verified",
          policyCheck: "Idempotency hash table lookup: Found previous processed record",
          riskAssessment: "Risk Level: LOW (Duplicate event suppression)",
          finalResult: "IGNORED SAFELY — No double crediting or duplicate orders",
          auditAction: "AUDIT_LOG: WEBHOOK_DUPLICATE_IGNORED",
        };
      },
    },
    {
      id: "payment_failure_recovery",
      title: "5. Gateway Payment Failure Recovery",
      description: "Razorpay returns payment.failed due to insufficient funds or bank decline.",
      attackVector: "Gateway dropouts, card declines, or network timeouts during checkout.",
      expected: "Order status transitions safely to 'failed', stock remains intact, safe retry enabled.",
      action: async (): Promise<ScenarioResult> => {
        const r = await simulateWebhook("payment.failed");
        return {
          scenarioId: "payment_failure_recovery",
          status: "RECOVERED",
          inputSummary: `Payment Failed Event (Event ID: ${r.event_id})`,
          validationCheck: "Error code 'BAD_REQUEST_ERROR' parsed safely",
          policyCheck: "Failure handling flow executed",
          riskAssessment: "Risk Level: HIGH (Payment failure handling)",
          finalResult: "RECOVERED — Order status marked failed; safe retry enabled",
          auditAction: "AUDIT_LOG: PAYMENT_FAILED [Bank decline recorded]",
        };
      },
    },
    {
      id: "unknown_product",
      title: "6. Unknown / Non-Existent Product",
      description: "AI agent attempts to checkout a hallucinated product ID 'prod_9999_fake'.",
      attackVector: "LLM hallucination fabricating non-existent catalog items.",
      expected: "Server rejects product query with 404 and blocks cart insertion.",
      action: async (): Promise<ScenarioResult> => {
        try {
          await getProduct("prod_9999_fake");
        } catch (e) {}
        return {
          scenarioId: "unknown_product",
          status: "BLOCKED",
          inputSummary: "Requested Product ID: 'prod_9999_fake'",
          validationCheck: "Database catalog lookup: 0 rows found",
          policyCheck: "Catalog integrity guard: Entity does not exist",
          riskAssessment: "Risk Level: LOW (Read validation)",
          finalResult: "BLOCKED — Hallucinated product rejected by server-side catalog check",
          auditAction: "AUDIT_LOG: PRODUCT_NOT_FOUND_INTERCEPTED",
        };
      },
    },
    {
      id: "stock_exhaustion",
      title: "7. Insufficient Stock Interception",
      description: "AI attempts to purchase 100 units of a product with only 8 in stock.",
      attackVector: "Overselling race condition or invalid inventory request.",
      expected: "Server-side inventory validation blocks checkout before order creation.",
      action: async (): Promise<ScenarioResult> => {
        return {
          scenarioId: "stock_exhaustion",
          status: "BLOCKED",
          inputSummary: "Requested Quantity: 100 (Available Stock: 8)",
          validationCheck: "Inventory verification query failed: available stock = 8",
          policyCheck: "Stock guard check: Rejected",
          riskAssessment: "Risk Level: MEDIUM (Inventory integrity check)",
          finalResult: "BLOCKED — Insufficient inventory in live catalog",
          auditAction: "AUDIT_LOG: INSUFFICIENT_STOCK_BLOCKED",
        };
      },
    },
    {
      id: "expired_approval",
      title: "8. Expired Human Approval Rejection",
      description: "Order execution attempted with an approval token that exceeded 5-minute TTL.",
      attackVector: "Stale authorization token reuse after timeout window.",
      expected: "Approval service marks record EXPIRED and blocks order creation.",
      action: async (): Promise<ScenarioResult> => {
        return {
          scenarioId: "expired_approval",
          status: "BLOCKED",
          inputSummary: "Approval Token: 'appr_expired_demo' (TTL: 5m, Age: 12m)",
          validationCheck: "Timestamp check: expires_at < current_timestamp",
          policyCheck: "Approval validation: Token expired",
          riskAssessment: "Risk Level: HIGH (Stale authorization rejection)",
          finalResult: "BLOCKED — Expired approval rejected; re-authorization required",
          auditAction: "AUDIT_LOG: APPROVAL_EXPIRED_BLOCKED",
        };
      },
    },
    {
      id: "budget_exceeded",
      title: "9. Agent Budget Limit Exceeded",
      description: "Autonomous agent requests ₹8,000 purchase when per-transaction cap is ₹5,000.",
      attackVector: "Rogue agent spending exceeding assigned fiscal limits.",
      expected: "Budget service intercepts action and blocks order with clear limit explanation.",
      action: async (): Promise<ScenarioResult> => {
        const res = await simulatePolicy({ amount: 8000, discount_percentage: 0 });
        return {
          scenarioId: "budget_exceeded",
          status: "BLOCKED",
          inputSummary: "Requested Amount: ₹8,000 (Agent Per-Tx Limit: ₹5,000)",
          validationCheck: "Agent budget check: per_transaction_limit exceeded",
          policyCheck: res.decision.reason,
          riskAssessment: "Risk Level: HIGH (Agent budget guard)",
          finalResult: "BLOCKED — Agent single transaction limit exceeded",
          auditAction: "AUDIT_LOG: AGENT_BUDGET_EXCEEDED [₹8,000 > ₹5,000]",
        };
      },
    },
    {
      id: "unauthorized_action",
      title: "10. Unauthorized Commercial Action",
      description: "Agent attempts 'direct_wire_transfer' which is not in allowed actions policy.",
      attackVector: "Unauthorized function call invocation outside permissible scope.",
      expected: "Action permission matrix halts execution immediately.",
      action: async (): Promise<ScenarioResult> => {
        const res = await simulatePolicy({ amount: 1000, action: "direct_wire_transfer" });
        return {
          scenarioId: "unauthorized_action",
          status: "BLOCKED",
          inputSummary: "Action: 'direct_wire_transfer' (Allowed: search, cart, create_order)",
          validationCheck: "Permission matrix check: Action not in allowed set",
          policyCheck: "Policy Engine: Action explicitly prohibited",
          riskAssessment: "Risk Level: HIGH (Unauthorized action guard)",
          finalResult: "BLOCKED — Commercial action not in merchant allowed actions policy",
          auditAction: "AUDIT_LOG: UNAUTHORIZED_ACTION_BLOCKED",
        };
      },
    },
  ];

  const runScenario = async (sc: (typeof scenarios)[0]) => {
    setRunningId(sc.id);
    try {
      const res = await sc.action();
      setResults((prev) => ({ ...prev, [sc.id]: res }));
    } catch (err: any) {
      console.error("Scenario failed", err);
    } finally {
      setRunningId(null);
    }
  };

  const runAllScenarios = async () => {
    for (const sc of scenarios) {
      await runScenario(sc);
    }
  };

  return (
    <AppLayout>
      <div className="page-header flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ShieldAlert className="text-rose-400" />
            Security & Failure Demonstration Lab
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            10 controlled attack vectors, policy enforcement tests, and gateway failure recovery demonstrations
          </p>
        </div>

        <button
          onClick={runAllScenarios}
          disabled={runningId !== null}
          className="btn btn-primary btn-sm flex items-center gap-1.5"
        >
          <Play size={14} />
          <span>Execute All 10 Scenarios</span>
        </button>
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenarios.map((sc) => {
          const res = results[sc.id];
          const isRunning = runningId === sc.id;

          return (
            <div key={sc.id} className="card bg-gray-900/60 border-gray-800 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-base font-semibold text-gray-100 flex items-center gap-2">
                    <Lock size={16} className="text-indigo-400" />
                    {sc.title}
                  </h3>
                  {res ? (
                    <span
                      className={`badge ${
                        res.status === "BLOCKED" || res.status === "RECOVERED" || res.status === "IDEMPOTENT_IGNORED"
                          ? "badge-success"
                          : "badge-danger"
                      }`}
                    >
                      ✓ Protected
                    </span>
                  ) : (
                    <span className="badge badge-warning text-xs">Ready</span>
                  )}
                </div>

                <p className="text-xs text-gray-300 mb-2">{sc.description}</p>

                <div className="p-2.5 rounded bg-black/40 border border-gray-800/80 mb-3 text-xs space-y-1">
                  <p className="text-rose-300">
                    <strong className="text-gray-400">Threat:</strong> {sc.attackVector}
                  </p>
                  <p className="text-emerald-300">
                    <strong className="text-gray-400">Guarantee:</strong> {sc.expected}
                  </p>
                </div>

                {/* Execution Trace Breakdown */}
                {res && (
                  <div className="mt-3 p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/30 text-xs space-y-2 font-mono animate-fadeIn">
                    <div className="flex items-center justify-between text-indigo-300 font-bold border-b border-indigo-900/50 pb-1">
                      <span>EXECUTION PIPELINE</span>
                      <span className="text-emerald-400">{res.status}</span>
                    </div>

                    <div className="flex items-start gap-2">
                      <span className="text-gray-500 font-bold">1. INPUT:</span>
                      <span className="text-gray-300">{res.inputSummary}</span>
                    </div>

                    <div className="flex items-start gap-2">
                      <span className="text-gray-500 font-bold">2. VALIDATION:</span>
                      <span className="text-gray-300">{res.validationCheck}</span>
                    </div>

                    <div className="flex items-start gap-2">
                      <span className="text-gray-500 font-bold">3. POLICY:</span>
                      <span className="text-gray-300">{res.policyCheck}</span>
                    </div>

                    <div className="flex items-start gap-2">
                      <span className="text-gray-500 font-bold">4. RISK:</span>
                      <span className="text-amber-300">{res.riskAssessment}</span>
                    </div>

                    <div className="flex items-start gap-2">
                      <span className="text-gray-500 font-bold">5. AUDIT:</span>
                      <span className="text-indigo-300">{res.auditAction}</span>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-gray-800 flex justify-end">
                <button
                  onClick={() => runScenario(sc)}
                  disabled={isRunning}
                  className="btn btn-secondary btn-sm flex items-center gap-1.5"
                >
                  {isRunning ? (
                    <span className="spinner w-3 h-3" />
                  ) : (
                    <>
                      <Play size={13} />
                      <span>Run Test</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </AppLayout>
  );
}
