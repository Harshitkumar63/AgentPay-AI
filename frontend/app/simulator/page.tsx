"use client";

import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import {
  Calculator,
  TrendingUp,
  Sliders,
  DollarSign,
  Package,
  CheckCircle2,
  AlertTriangle,
  Info,
  RefreshCw,
} from "lucide-react";
import { simulateWhatIf } from "@/services/api";
import { BusinessSimulation } from "@/types";

export default function BusinessSimulatorPage() {
  const [discountPct, setDiscountPct] = useState(10);
  const [inventoryIncreasePct, setInventoryIncreasePct] = useState(15);
  const [priceAdjustmentPct, setPriceAdjustmentPct] = useState(0);
  const [promotedCategory, setPromotedCategory] = useState("shoes");
  const [simulation, setSimulation] = useState<BusinessSimulation | null>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    try {
      setLoading(true);
      const res = await simulateWhatIf({
        discount_percentage: discountPct,
        inventory_increase_percentage: inventoryIncreasePct,
        price_adjustment_percentage: priceAdjustmentPct,
        promoted_category: promotedCategory,
      });
      setSimulation(res);
    } catch (err: any) {
      alert(err.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [discountPct, inventoryIncreasePct, priceAdjustmentPct, promotedCategory]);

  return (
    <AppLayout>
      <div className="page-header mb-6">
        <div className="flex items-center gap-2">
          <Calculator size={24} className="text-blue-400" />
          <h1 className="page-title text-2xl font-bold text-white">What-If Business Simulator</h1>
        </div>
        <p className="page-subtitle text-slate-400 text-sm mt-1">
          Model commercial strategies, promotional discounts, and inventory expansion to forecast revenue, volume, and profit margins.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Controls Column */}
        <div className="lg:col-span-5 space-y-6">
          <div className="card space-y-5">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Sliders size={16} className="text-blue-400" />
              Hypothetical Parameters
            </h2>

            {/* Discount Depth */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-400">Promotional Discount</span>
                <span className="font-bold text-blue-400 font-mono">{discountPct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="1"
                value={discountPct}
                onChange={(e) => setDiscountPct(parseInt(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>

            {/* Inventory Scaling */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-400">Inventory Capacity Expansion</span>
                <span className="font-bold text-emerald-400 font-mono">+{inventoryIncreasePct}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="5"
                value={inventoryIncreasePct}
                onChange={(e) => setInventoryIncreasePct(parseInt(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>

            {/* Price Index Adjustment */}
            <div>
              <div className="flex justify-between items-center text-xs mb-1.5">
                <span className="font-semibold text-slate-400">Catalog Price Movement</span>
                <span className="font-bold text-purple-400 font-mono">{priceAdjustmentPct >= 0 ? `+${priceAdjustmentPct}%` : `${priceAdjustmentPct}%`}</span>
              </div>
              <input
                type="range"
                min="-20"
                max="20"
                step="2"
                value={priceAdjustmentPct}
                onChange={(e) => setPriceAdjustmentPct(parseInt(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            {/* Promoted Category */}
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Focus Campaign Category</label>
              <select
                value={promotedCategory}
                onChange={(e) => setPromotedCategory(e.target.value)}
                className="w-full bg-slate-950 p-2.5 rounded-lg border border-slate-800 text-xs text-white focus:border-blue-500 focus:outline-none"
              >
                <option value="shoes">Running & Athletic Shoes</option>
                <option value="electronics">Laptops & Electronics</option>
                <option value="fitness">Fitness & Hydration Gear</option>
                <option value="bags">Travel & Commuter Bags</option>
              </select>
            </div>
          </div>
        </div>

        {/* Forecast Column */}
        <div className="lg:col-span-7">
          {simulation ? (
            <div className="card space-y-6 bg-slate-900/60 border border-slate-800">
              {/* Projected Revenue Comparison */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Baseline 30-Day Revenue</div>
                  <div className="text-xl font-bold text-slate-300 mt-1">₹{simulation.baseline_revenue.toLocaleString()}</div>
                  <div className="text-xs text-slate-500 mt-0.5">{simulation.baseline_order_volume} Orders</div>
                </div>

                <div className="p-4 bg-slate-950 rounded-xl border border-blue-500/30 text-center">
                  <div className="text-[10px] text-blue-400 uppercase font-semibold">Estimated Projected Revenue</div>
                  <div className="text-xl font-extrabold text-white mt-1">₹{simulation.estimated_revenue.toLocaleString()}</div>
                  <div className="text-xs text-emerald-400 font-semibold mt-0.5">
                    {simulation.revenue_delta_percentage >= 0 ? `+${simulation.revenue_delta_percentage}%` : `${simulation.revenue_delta_percentage}%`} ({simulation.estimated_order_volume} Orders)
                  </div>
                </div>
              </div>

              {/* Order Volume & Margin Metrics */}
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Order Volume Lift</div>
                  <div className="text-base font-bold text-emerald-400">
                    {simulation.order_volume_delta_percentage >= 0 ? `+${simulation.order_volume_delta_percentage}%` : `${simulation.order_volume_delta_percentage}%`}
                  </div>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">Projected Net Margin</div>
                  <div className="text-base font-bold text-purple-400">{simulation.estimated_margin_percentage}%</div>
                </div>
              </div>

              {/* Strategic Insights */}
              <div>
                <h3 className="text-xs font-bold text-slate-300 mb-2">Simulated Strategy Insights</h3>
                <div className="space-y-2">
                  {simulation.insights.map((insight, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                      <CheckCircle2 size={15} className="text-emerald-400 shrink-0 mt-0.5" />
                      <span>{insight}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
                <Info size={15} className="text-blue-400 shrink-0 mt-0.5" />
                <span>{simulation.disclaimer}</span>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </AppLayout>
  );
}
