"use client";

import React from "react";
import {
  PieChart as PieIcon,
  CheckCircle2,
  AlertTriangle,
  IndianRupee,
  Users,
  Info,
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

export function BudgetTab() {
  const { trip } = useTripStore();

  if (!trip) return null;

  const perAdultCost = Math.round(
    trip.budget.estimated_total / trip.travelers.count
  );

  const barChartData = trip.budget.categories.map((c) => ({
    category: c.name.split("(")[0].trim(),
    amount: c.amount,
  }));

  return (
    <div className="space-y-6">
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
                ? `Total estimated expenses across flights, boutique hotels, AC cab transit, meals and activities total ₹${trip.budget.estimated_total.toLocaleString()}, leaving a contingency reserve buffer of ₹${trip.budget.difference.toLocaleString()}.`
                : `The estimated total exceeds the allocated budget. Consider adjusting stay categories or flight booking dates.`}
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
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: cat.color }}
                  />
                  <span>{cat.name.split("(")[0].trim()}</span>
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
              Itemized estimates based on real-time provider quotations
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
              Food estimate accounts for ₹570/person/day (traditional Sadya, coastal fish delicacies, and hotel dining).
              Transport accounts for private air-conditioned sedan throughout the 7 days including all highway tolls and hill station parking permits.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

