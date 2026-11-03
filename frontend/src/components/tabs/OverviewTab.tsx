"use client";

import React from "react";
import {
  Plane,
  Building2,
  Car,
  Compass,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  CloudSun,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { useTripStore } from "../../store/useTripStore";

export function OverviewTab() {
  const { trip, setActiveTab } = useTripStore();

  if (!trip) return null;

  const budgetChartData = trip.budget.categories.map((c) => ({
    name: c.name.split("(")[0].trim(),
    value: c.amount,
    color: c.color,
  }));

  const flightCategory = trip.budget.categories.find((c) =>
    c.name.toLowerCase().includes("flight")
  );
  const hotelCategory = trip.budget.categories.find((c) =>
    c.name.toLowerCase().includes("hotel")
  );
  const transportCategory = trip.budget.categories.find(
    (c) =>
      c.name.toLowerCase().includes("transport") ||
      c.name.toLowerCase().includes("cab")
  );
  const activityCategory = trip.budget.categories.find(
    (c) =>
      c.name.toLowerCase().includes("sightseeing") ||
      c.name.toLowerCase().includes("activit")
  );

  const mainFlight = trip.flights[0] || {
    origin: "Origin",
    destination: trip.destinations[0] || "Destination",
    airline: "Verified Airline",
    duration: "Direct",
  };

  const totalDrivingKm = trip.routes.reduce(
    (acc, r) => acc + (r.distance_km || 0),
    0
  );

  const totalActivities = trip.itinerary.reduce(
    (acc, d) => acc + (d.activities?.length || 0),
    0
  );

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-8">
      {/* LEFT COLUMN: Overview, Compact Cards, Preview Days 1-3 */}
      <div className="lg:col-span-7 space-y-6">
        {/* Short Trip Overview */}
        <div className="bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-2xs">
          <h3 className="text-base font-semibold text-stone-900 mb-2.5 flex items-center gap-2">
            <Compass className="h-4 w-4 text-[#1B4332]" />
            <span>Trip Overview</span>
          </h3>
          <p className="text-sm text-stone-600 leading-relaxed font-normal">
            {trip.overview}
          </p>

          <div className="mt-4 pt-4 border-t border-stone-100 flex flex-wrap items-center gap-4 text-xs text-stone-500">
            <span className="flex items-center gap-1.5 text-emerald-800 font-medium">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Verified with HasData Google Hotels & Flight GDS
            </span>
          </div>
        </div>

        {/* Dynamic Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {/* Flights Summary */}
          <div className="bg-white rounded-xl border border-stone-200/80 p-4 shadow-2xs flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
                  Flights
                </span>
                {trip.flights && trip.flights.length > 0 ? (
                  <>
                    <p className="text-sm font-semibold text-stone-900 mt-1">
                      {trip.flights[0].origin} ⇄ {trip.flights[0].destination}
                    </p>
                    <p className="text-xs text-stone-500 mt-0.5">
                      {trip.flights[0].airline} • {trip.flights[0].duration || "Non-stop"}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-stone-700 mt-1">
                      No Flights Found
                    </p>
                    <p className="text-xs text-amber-600 mt-0.5">
                      Check Economy class
                    </p>
                  </>
                )}
              </div>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-[#1B4332] flex items-center justify-center">
                <Plane className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between text-xs">
              <span className="text-stone-500">{trip.flights && trip.flights.length > 0 ? `Total for ${trip.travelers.count}:` : "Status:"}</span>
              <span className="font-semibold text-stone-900">
                {trip.flights && trip.flights.length > 0 ? `₹${(flightCategory?.amount || 0).toLocaleString()}` : "Not Found"}
              </span>
            </div>
          </div>

          {/* Accommodation Summary */}
          <div className="bg-white rounded-xl border border-stone-200/80 p-4 shadow-2xs flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
                  Hotels & Stays
                </span>
                <p className="text-sm font-semibold text-stone-900 mt-1">
                  {trip.hotels.length} Verified Stays
                </p>
                <p className="text-xs text-stone-500 mt-0.5">
                  {trip.destinations.join(", ")} • Live Rates
                </p>
              </div>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-[#1B4332] flex items-center justify-center">
                <Building2 className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between text-xs">
              <span className="text-stone-500">Total Stays:</span>
              <span className="font-semibold text-stone-900">
                ₹{(hotelCategory?.amount || 0).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Transport Summary */}
          <div className="bg-white rounded-xl border border-stone-200/80 p-4 shadow-2xs flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
                  Ground Transport
                </span>
                <p className="text-sm font-semibold text-stone-900 mt-1">
                  Private AC Sedan ({trip.travel_dates.duration_days} Days)
                </p>
                <p className="text-xs text-stone-500 mt-0.5">
                  {totalDrivingKm > 0 ? `${totalDrivingKm} km Inter-City Routes` : "Local & Scenic Transfers"}
                </p>
              </div>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-[#1B4332] flex items-center justify-center">
                <Car className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between text-xs">
              <span className="text-stone-500">Cab & Transfers:</span>
              <span className="font-semibold text-stone-900">
                ₹{(transportCategory?.amount || 0).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Activities Summary */}
          <div className="bg-white rounded-xl border border-stone-200/80 p-4 shadow-2xs flex flex-col justify-between">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
                  Sightseeing & Activities
                </span>
                <p className="text-sm font-semibold text-stone-900 mt-1">
                  {totalActivities} Curated Experiences
                </p>
                <p className="text-xs text-stone-500 mt-0.5 truncate max-w-[150px]">
                  {trip.destinations.join(" & ")}
                </p>
              </div>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-[#1B4332] flex items-center justify-center">
                <Compass className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between text-xs">
              <span className="text-stone-500">Passes & Tours:</span>
              <span className="font-semibold text-stone-900">
                ₹{(activityCategory?.amount || 0).toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Day-wise Itinerary Preview (First 3 Days) */}
        <div className="bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-2xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-stone-900">
                Itinerary Preview (Days 1–{Math.min(3, trip.itinerary.length)})
              </h3>
              <p className="text-xs text-stone-500 mt-0.5">
                First leg of your journey in {trip.destinations[0]}
              </p>
            </div>
            <button
              onClick={() => setActiveTab("itinerary")}
              className="text-xs font-semibold text-emerald-800 hover:text-emerald-900 flex items-center gap-1 group cursor-pointer"
            >
              <span>View Full Itinerary</span>
              <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>

          <div className="space-y-3">
            {trip.itinerary.slice(0, 3).map((day, idx) => (
              <div
                key={`overview-day-${day.day || idx}`}
                className="p-3.5 rounded-xl bg-stone-50/70 border border-stone-200/60 hover:bg-stone-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-[11px] font-semibold bg-[#1B4332] text-white rounded-md">
                      Day {day.day}
                    </span>
                    <span className="text-xs font-medium text-stone-500">
                      {day.date} • {day.destination}
                    </span>
                  </div>
                </div>
                <h4 className="text-sm font-semibold text-stone-900 mt-1.5">
                  {day.title}
                </h4>
                <p className="text-xs text-stone-600 mt-1 line-clamp-2">
                  {day.summary}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-5 pt-4 border-t border-stone-100 text-center">
            <button
              onClick={() => setActiveTab("itinerary")}
              className="w-full sm:w-auto px-5 py-2.5 bg-stone-100 hover:bg-stone-200/80 text-stone-800 text-xs font-medium rounded-xl inline-flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <span>Explore All {trip.itinerary.length} Days in Full Itinerary</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN: Budget Summary Card & Recharts Donut Visualization */}
      <div className="lg:col-span-5 space-y-6">
        {/* Budget Summary Card */}
        <div className="bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-6 shadow-2xs">
          <div className="flex items-center justify-between pb-3 border-b border-stone-100">
            <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
              Budget Performance
            </span>
            <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              trip.budget.is_within_budget
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-rose-50 text-rose-800 border border-rose-200"
            }`}>
              <CheckCircle2 className="h-3 w-3" />
              {trip.budget.status_label}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4">
            <div className="p-3.5 rounded-xl bg-stone-50/70 border border-stone-200/50">
              <span className="text-xs text-stone-500">User Budget</span>
              <p className="text-lg font-bold text-stone-900 mt-0.5">
                {trip.budget.currency_symbol}
                {trip.budget.user_budget.toLocaleString()}
              </p>
            </div>
            <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-100">
              <span className="text-xs text-emerald-800 font-medium">Estimated Total</span>
              <p className="text-lg font-bold text-[#1B4332] mt-0.5">
                {trip.budget.currency_symbol}
                {trip.budget.estimated_total.toLocaleString()}
              </p>
            </div>
          </div>

          <div className={`mt-3.5 p-3 rounded-xl text-xs flex items-center justify-between ${
            trip.budget.is_within_budget
              ? "bg-emerald-50 text-emerald-900"
              : "bg-rose-50 text-rose-900"
          }`}>
            <span className="flex items-center gap-1.5 font-medium">
              {trip.budget.is_within_budget ? (
                <TrendingDown className="h-4 w-4 text-emerald-700" />
              ) : (
                <TrendingUp className="h-4 w-4 text-rose-700" />
              )}
              {trip.budget.is_within_budget ? "Remaining Buffer:" : "Deficit Amount:"}
            </span>
            <span className="font-bold text-sm">
              {trip.budget.is_within_budget ? "+" : "-"}
              {trip.budget.currency_symbol}
              {trip.budget.difference.toLocaleString()}
            </span>
          </div>

          {/* Recharts Budget Donut Visualization */}
          <div className="mt-5">
            <h4 className="text-xs font-semibold text-stone-700 mb-2">
              Expense Allocation Breakdown
            </h4>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={budgetChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={46}
                    outerRadius={68}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {budgetChartData.map((entry, index) => (
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

            <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-stone-100 text-[11px]">
              {trip.budget.categories.slice(0, 4).map((c, idx) => (
                <div key={`overview-budget-cat-${c.name}-${idx}`} className="flex items-center gap-1.5">
                  <span
                    className="h-2.5 w-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: c.color }}
                  />
                  <span className="truncate text-stone-600">
                    {c.name.split("(")[0].trim()}
                  </span>
                  <span className="ml-auto font-medium text-stone-900">
                    {c.percentage}%
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-4 text-center">
              <button
                onClick={() => setActiveTab("budget")}
                className="text-xs font-medium text-emerald-800 hover:text-emerald-900 cursor-pointer"
              >
                View Detailed Itemized Budget Breakdown →
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Weather Highlights Card */}
        {trip.weather && trip.weather.length > 0 && (
          <div className="bg-white rounded-2xl border border-stone-200/80 p-5 shadow-2xs">
            <div className="flex items-center justify-between pb-2 border-b border-stone-100">
              <div className="flex items-center gap-2">
                <CloudSun className="h-4 w-4 text-amber-500" />
                <span className="text-xs font-semibold text-stone-800">
                  Destination Weather Highlights
                </span>
              </div>
              <span className="text-[10px] text-stone-400">Live Observation</span>
            </div>

            <div className="grid grid-cols-3 gap-2 mt-3 text-center">
              {trip.weather.slice(0, 3).map((w, idx) => (
                <div key={`overview-weather-${w.city || "city"}-${idx}`} className="p-2.5 rounded-xl bg-stone-50 border border-stone-100">
                  <span className="text-xs font-semibold text-stone-900 block truncate">
                    {w.city}
                  </span>
                  <span className="text-lg font-bold text-stone-800 block my-0.5">
                    {w.temperature_c}°C
                  </span>
                  <span className="text-[11px] text-stone-500 block truncate">
                    {w.condition}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
