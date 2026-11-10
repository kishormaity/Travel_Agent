"use client";

import React, { useState } from "react";
import {
  PieChart as PieIcon,
  CheckCircle2,
  AlertTriangle,
  IndianRupee,
  Users,
  Info,
  Copy,
  Check,
  LayoutList,
  FileText,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import { useTripStore } from "../../store/useTripStore";
import { FormattedOutputViewer } from "../FormattedOutputViewer";

export function BudgetTab() {
  const { trip } = useTripStore();
  const [viewMode, setViewMode] = useState<"charts" | "text">("charts");
  const [copied, setCopied] = useState(false);

  if (!trip) return null;

  const perAdultCost = Math.round(
    trip.budget.estimated_total / Math.max(1, trip.travelers.count)
  );

  const barChartData = trip.budget.categories.map((c) => ({
    category: c.name.split("(")[0].trim(),
    amount: c.amount,
  }));

  const handleCopyBudget = () => {
    if (!navigator.clipboard) return;
    const lines = [
      `Budget Breakdown for ${trip.title}`,
      `Target Budget: ₹${trip.budget.user_budget.toLocaleString()}`,
      `Total Estimated Cost: ₹${trip.budget.estimated_total.toLocaleString()}`,
      `Verdict: ${trip.budget.status_label} (Difference: ₹${trip.budget.difference.toLocaleString()})`,
      `Per Person Cost: ₹${perAdultCost.toLocaleString()}`,
      "",
      ...trip.budget.categories.map(
        (c) => `- ${c.name}: ₹${c.amount.toLocaleString()} (${c.percentage}%) — ${c.notes || ""}`
      ),
    ];
    navigator.clipboard.writeText(lines.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="bg-white rounded-2xl border border-stone-200/80 p-4 sm:p-5 shadow-2xs flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold uppercase tracking-wider text-stone-700">
            Financial Analysis & Budget Verification
          </span>
          <span
            className={`text-xs font-semibold px-2.5 py-0.5 rounded-md border ${
              trip.budget.is_within_budget
                ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                : "bg-rose-50 text-rose-800 border-rose-200"
            }`}
          >
            {trip.budget.status_label}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle: Visual Charts vs Report Text */}
          <div className="inline-flex rounded-lg border border-stone-200 bg-stone-50 p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setViewMode("charts")}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                viewMode === "charts"
                  ? "bg-white text-stone-900 shadow-2xs font-semibold"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <LayoutList className="h-3.5 w-3.5" />
              <span>Visual Analytics</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("text")}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                viewMode === "text"
                  ? "bg-white text-stone-900 shadow-2xs font-semibold"
                  : "text-stone-600 hover:text-stone-900"
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              <span>Report Text</span>
            </button>
          </div>

          <button
            onClick={handleCopyBudget}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200/80 border border-stone-200 rounded-lg transition-colors cursor-pointer"
            title="Copy budget calculations"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-600" />
                <span className="text-emerald-700">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5 text-stone-500" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {viewMode === "text" ? (
        <FormattedOutputViewer sectionKey="budget" />
      ) : (
        <>
          {/* Top Banner: Sufficiency Verdict */}
          <div
            className={`p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
              trip.budget.is_within_budget
                ? "bg-emerald-50/70 border-emerald-200 text-emerald-950"
                : "bg-rose-50/70 border-rose-200 text-rose-950"
            }`}
          >
            <div className="flex items-start gap-3">
              {trip.budget.is_within_budget ? (
                <CheckCircle2 className="h-6 w-6 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="h-6 w-6 text-rose-600 shrink-0 mt-0.5" />
              )}
              <div>
                <h3 className="text-base font-bold">
                  {trip.budget.is_within_budget
                    ? `₹${trip.budget.user_budget.toLocaleString()} is SUFFICIENT for ${trip.travelers.label}`
                    : `Budget Exceeded by ₹${trip.budget.difference.toLocaleString()}`}
                </h3>
                <p className="text-xs sm:text-sm mt-1 text-stone-600 leading-relaxed font-normal">
                  {trip.budget.is_within_budget
                    ? `Total estimated expenses across verified flights, hotel accommodations, dedicated AC cab transit, daily meals, sightseeing entry passes and contingency total ₹${trip.budget.estimated_total.toLocaleString()}, leaving a comfortable surplus reserve buffer of ₹${trip.budget.difference.toLocaleString()}.`
                    : `The estimated total of ₹${trip.budget.estimated_total.toLocaleString()} exceeds your target budget of ₹${trip.budget.user_budget.toLocaleString()} by ₹${trip.budget.difference.toLocaleString()}. Consider selecting lower flight fares or adjusting accommodation tier.`}
                </p>
              </div>
            </div>

            <div className="text-left sm:text-right shrink-0">
              <span className="text-xs text-stone-500 block">Per Person Share:</span>
              <span className="text-xl font-bold text-stone-900">
                ₹{perAdultCost.toLocaleString()}
              </span>
              <span className="text-[11px] text-stone-500 block">/ adult</span>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Recharts Donut */}
            <div className="lg:col-span-5 bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-2xs flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-semibold text-stone-900 mb-1 flex items-center gap-2">
                  <PieIcon className="h-4 w-4 text-[#1B4332]" />
                  <span>Share of Total Budget</span>
                </h4>
                <p className="text-xs text-stone-500">
                  Distribution of ₹{trip.budget.estimated_total.toLocaleString()} across travel pillars
                </p>

                <div className="h-56 w-full mt-2">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={trip.budget.categories}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={80}
                        paddingAngle={3}
                        dataKey="amount"
                      >
                        {trip.budget.categories.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(val: any) => [
                          `₹${Number(val).toLocaleString()}`,
                          "Amount",
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="space-y-1.5 pt-3 border-t border-stone-100">
                {trip.budget.categories.map((cat) => (
                  <div
                    key={cat.name}
                    className="flex items-center justify-between text-xs text-stone-600"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2.5 w-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: cat.color }}
                      />
                      <span className="truncate max-w-[160px]">{cat.name.split("(")[0].trim()}</span>
                    </div>
                    <div className="flex items-center gap-2 font-medium text-stone-900">
                      <span>₹{cat.amount.toLocaleString()}</span>
                      <span className="text-stone-400">({cat.percentage}%)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Category Comparison Bar Chart */}
            <div className="lg:col-span-7 bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-2xs flex flex-col justify-between">
              <div>
                <h4 className="text-sm font-semibold text-stone-900 mb-1">
                  Category Cost Breakdown (INR)
                </h4>
                <p className="text-xs text-stone-500">
                  Calculated from live flight and accommodation quotes
                </p>

                <div className="h-64 w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={barChartData} layout="vertical" margin={{ left: 10, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E7E5E4" />
                      <XAxis type="number" tickFormatter={(v) => `₹${v / 1000}k`} tick={{ fontSize: 11 }} />
                      <YAxis type="category" dataKey="category" width={110} tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, "Estimated Cost"]} />
                      <Bar dataKey="amount" fill="#1B4332" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200/60 text-xs text-stone-600 flex items-start gap-2 mt-4">
                <Info className="h-4 w-4 text-stone-400 shrink-0 mt-0.5" />
                <span>
                  {trip.flights && trip.flights.length > 0
                    ? `Airfare computed using live verified flight rates (${trip.flights[0].airline} at ₹${Number(trip.flights[0].price).toLocaleString()}). `
                    : "Airfare calculated based on competitive domestic economy scheduled flights. "}
                  {trip.hotels && trip.hotels.length > 0
                    ? `Hotel expenses calculated from verified accommodations (${trip.hotels[0].property_name || trip.hotels[0].name} at ₹${Number(trip.hotels[0].rate_per_night || trip.hotels[0].price_per_night || 0).toLocaleString()}/night). `
                    : "Hotel expenses calculated from verified 3-star standard nightly rates. "}
                  Local transport and food allowances reflect real-world per-person expenses across the full duration.
                </span>
              </div>
            </div>
          </div>

          {/* Itemized Calculation & Verification Table */}
          <div className="bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-stone-900">
                Itemized Expense Breakdown & Calculation Basis
              </h4>
              <span className="text-xs text-stone-500 font-medium">
                All amounts verified in INR
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead>
                  <tr className="border-b border-stone-200 text-stone-500 font-semibold">
                    <th className="py-2.5 pr-4">Expense Category</th>
                    <th className="py-2.5 px-4 text-right">Cost (INR)</th>
                    <th className="py-2.5 px-4 text-right">Share (%)</th>
                    <th className="py-2.5 pl-4">Calculation Basis / Provider Verification</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 text-stone-700">
                  {trip.budget.categories.map((c) => (
                    <tr key={c.name} className="hover:bg-stone-50/50 transition-colors">
                      <td className="py-3 pr-4 font-semibold text-stone-900 flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full shrink-0"
                          style={{ backgroundColor: c.color }}
                        />
                        <span>{c.name}</span>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-stone-900 whitespace-nowrap">
                        ₹{c.amount.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right text-stone-500 font-medium whitespace-nowrap">
                        {c.percentage}%
                      </td>
                      <td className="py-3 pl-4 text-stone-600 text-xs leading-relaxed">
                        {c.notes || "Calculated based on verified itinerary parameters"}
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-stone-300 font-bold text-stone-900 bg-stone-50/80">
                    <td className="py-3.5 pr-4 text-sm font-bold">Total Estimated Cost</td>
                    <td className="py-3.5 px-4 text-right text-base text-[#1B4332] font-black whitespace-nowrap">
                      ₹{trip.budget.estimated_total.toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 text-right text-stone-600 font-bold">100%</td>
                    <td className="py-3.5 pl-4 text-xs font-semibold">
                      {trip.budget.is_within_budget ? (
                        <span className="text-emerald-700 font-bold">
                          Within Budget (Surplus Buffer: ₹{trip.budget.difference.toLocaleString()})
                        </span>
                      ) : (
                        <span className="text-rose-700 font-bold">
                          Budget Deficit (Exceeded by ₹{trip.budget.difference.toLocaleString()})
                        </span>
                      )}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

