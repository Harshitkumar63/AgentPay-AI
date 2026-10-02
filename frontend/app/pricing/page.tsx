"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  DollarSign,
  TrendingUp,
  Package,
  Sliders,
  Play,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  Info,
} from "lucide-react";
import { getProducts, simulatePricing } from "@/services/api";
import { Product, PricingSimulation } from "@/types";

export default function PricingSimulatorPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>("prod_001");
  const [demandMultiplier, setDemandMultiplier] = useState(1.2);
  const [competitorAdjustment, setCompetitorAdjustment] = useState(0.0);
  const [simulation, setSimulation] = useState<PricingSimulation | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function load() {
      const data = await getProducts();
      setProducts(data);
      if (data.length > 0) {
        setSelectedProductId(data[0].id);
      }
    }
    load();
  }, []);

  const runSimulation = async () => {
    try {
      setLoading(true);
      const res = await simulatePricing(selectedProductId, competitorAdjustment, demandMultiplier);
      setSimulation(res);
    } catch (err: any) {
      alert(err.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedProductId) {
      runSimulation();
    }
  }, [selectedProductId, demandMultiplier, competitorAdjustment]);

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <div className="flex items-center gap-2">
          <DollarSign size={24} className="text-blue-400" />
          <h1 className="page-title text-2xl font-bold text-white">Dynamic Pricing Simulator</h1>
        </div>
        <p className="page-subtitle text-slate-400 text-sm mt-1">
          Simulate market demand velocity and stock elasticity to optimize product pricing. Data is purely for forecasting and does not modify active database prices.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Simulation Controls */}
        <div className="lg:col-span-5 space-y-6">
          <div className="card space-y-5">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders size={16} className="text-blue-400" />
              Simulation Parameters
            </h2>

            {/* Product Selector */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Select Target Product</label>
              <select
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                className="w-full bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
              >
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (Stock: {p.stock}, Current: ₹{p.price.toLocaleString()})
                  </option>
                ))}
              </select>
            </div>

            {/* Demand Multiplier Slider */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-400">Demand Velocity Multiplier</span>
                <span className="font-bold text-blue-400 font-mono">{demandMultiplier}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="2.5"
                step="0.1"
                value={demandMultiplier}
                onChange={(e) => setDemandMultiplier(parseFloat(e.target.value))}
                className="w-full accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>0.5x (Low Demand)</span>
                <span>1.0x (Normal)</span>
                <span>2.5x (Peak Surge)</span>
              </div>
            </div>

            {/* Competitor Index Adjustment */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-400">Competitor Price Index Shift</span>
                <span className="font-bold text-emerald-400 font-mono">{competitorAdjustment > 0 ? `+${competitorAdjustment}%` : `${competitorAdjustment}%`}</span>
              </div>
              <input
                type="range"
                min="-15"
                max="15"
                step="1"
                value={competitorAdjustment}
                onChange={(e) => setCompetitorAdjustment(parseFloat(e.target.value))}
                className="w-full accent-emerald-500"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>-15% (Under-cutting)</span>
                <span>0% (Parity)</span>
                <span>+15% (Premium)</span>
              </div>
            </div>

            <button
              onClick={runSimulation}
              disabled={loading}
              className="btn btn-primary w-full py-2.5 text-xs font-bold flex items-center justify-center gap-2"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Recalculate Elasticity
            </button>
          </div>
        </div>

        {/* Simulation Output Result */}
        <div className="lg:col-span-7">
          {simulation ? (
            <div className="card space-y-6 bg-slate-900/60 border border-slate-800">
              {/* Proposal Header Banner */}
              <div className="flex justify-between items-start flex-wrap gap-4 p-4 bg-slate-950/80 rounded-xl border border-slate-800/80">
                <div>
                  <div className="text-[10px] text-slate-400 uppercase font-mono tracking-wider">Pricing Proposal</div>
                  <div className="text-xl font-bold text-white mt-0.5">{simulation.product_name}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    Live Stock: <strong className="text-white">{simulation.stock_level} units</strong>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-2xl font-extrabold text-blue-400">
                    ₹{simulation.suggested_price.toLocaleString()}
                  </div>
                  <div className="text-xs font-semibold text-slate-400">
                    Baseline: <span className="line-through">₹{simulation.current_price.toLocaleString()}</span> (
                    <span className={simulation.price_change_percentage >= 0 ? "text-emerald-400" : "text-amber-400"}>
                      {simulation.price_change_percentage >= 0 ? `+${simulation.price_change_percentage}%` : `${simulation.price_change_percentage}%`}
                    </span>)
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-center">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Elasticity Score</div>
                  <div className="text-base font-bold text-purple-400">{simulation.elasticity_score}</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Weekly Velocity</div>
                  <div className="text-base font-bold text-white">{simulation.weekly_sales_velocity} units/day</div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Est. Net Lift</div>
                  <div className="text-base font-bold text-emerald-400">+₹{simulation.estimated_revenue_impact.toLocaleString()}</div>
                </div>
              </div>

              {/* Strategic Reasoning */}
              <div>
                <h3 className="text-xs font-bold text-slate-300 mb-2">Algorithmic Reasoning</h3>
                <div className="space-y-2">
                  {simulation.reasons.map((r, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-slate-300 p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80">
                      <CheckCircle2 size={14} className="text-blue-400 shrink-0 mt-0.5" />
                      <span>{r}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300 flex items-start gap-2">
                <Info size={16} className="shrink-0 mt-0.5" />
                <span>{simulation.disclaimer}</span>
              </div>
            </div>
          ) : (
            <div className="card text-center py-24 text-slate-500">Select product to run pricing simulation</div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
