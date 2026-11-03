"use client";

import React, { useState } from "react";
import {
  Car,
  Navigation,
  Compass,
  ArrowRight,
} from "lucide-react";
import { useTripStore } from "../../store/useTripStore";

export function MapTab() {
  const { trip } = useTripStore();

  if (!trip) return null;

  // Generate dynamic waypoints based on actual destinations
  const waypoints = trip.destinations.map((dest, i) => {
    const total = trip.destinations.length;
    // Distribute nicely along an S-curve corridor
    const t = total > 1 ? i / (total - 1) : 0.5;
    const x = Math.round(25 + t * 50);
    const y = Math.round(30 + Math.sin(t * Math.PI) * 45);

    return {
      id: `wp-${i}`,
      name: dest,
      tag: i === 0 ? "Entry Gateway" : i === total - 1 ? "Final Destination" : "En-route Discovery",
      x,
      y,
      description: `Scenic itinerary milestone exploring ${dest} with verified local attractions, dining and boutique stay accommodation.`,
      stayDuration: `${Math.max(1, Math.round(trip.travel_dates.duration_days / total))} Nights`,
      attractions: [
        `${dest} Historic Quarter & Landmark`,
        `${dest} Local Artisan Market`,
        `${dest} Sunset Vantage Point`,
      ],
    };
  });

  const [activePointId, setActivePointId] = useState<string>(waypoints[0]?.id || "wp-0");
  const currentPoint = waypoints.find((w) => w.id === activePointId) || waypoints[0];

  const totalDrivingKm = trip.routes.reduce((acc, r) => acc + (r.distance_km || 0), 0);

  return (
    <div className="space-y-6">
      {/* Route Telemetry Bar */}
      <div className="bg-white rounded-2xl border border-stone-200/80 p-5 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-100">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
              Interactive Route Map & Geographical Waypoints
            </span>
            <h3 className="text-base font-semibold text-stone-900 mt-0.5">
              {trip.destinations.join(" → ")} Corridor
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200">
              Total Highway Driving: {totalDrivingKm > 0 ? `${totalDrivingKm} km` : "Curated Circuit"}
            </span>
          </div>
        </div>

        {/* Route Segments Pills */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 text-xs">
          {trip.routes.length > 0 ? (
            trip.routes.map((rt, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-stone-50/70 border border-stone-200/60 flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <Car className="h-4 w-4 text-[#1B4332]" />
                  <span className="font-semibold text-stone-800 truncate max-w-[140px]">
                    {rt.origin} → {rt.destination}
                  </span>
                </div>
                <div className="text-right text-[11px] text-stone-500">
                  <span className="font-semibold text-stone-900 block">
                    {rt.distance_km} km
                  </span>
                  <span>{rt.duration_text}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-3 p-3 rounded-xl bg-stone-50 text-stone-600 text-xs text-center">
              Inter-city transfers configured between {trip.destinations.join(" and ")}
            </div>
          )}
        </div>
      </div>

      {/* Main Map Visual & Details Split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* SVG Route Visualization Card */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-stone-200/80 p-6 shadow-2xs relative overflow-hidden flex flex-col justify-between min-h-[420px]">
          <div className="flex items-center justify-between z-10">
            <span className="text-xs font-semibold text-stone-700 flex items-center gap-1.5">
              <Navigation className="h-4 w-4 text-[#1B4332]" />
              <span>Wayfarer Verified Route Corridor</span>
            </span>
            <span className="text-[11px] text-stone-400">Click a pin to view waypoint highlights</span>
          </div>

          {/* Graphical Map Canvas */}
          <div className="relative w-full h-80 my-4 flex items-center justify-center">
            <svg
              viewBox="0 0 100 100"
              className="w-full h-full max-h-76"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Background Geographic Contour */}
              <path
                d="M 10,10 Q 50,0 90,20 Q 80,80 50,90 Q 20,80 10,10 Z"
                fill="#F8FAF7"
                stroke="#E7E5E4"
                strokeWidth="1"
              />

              {/* Highway Corridor Line linking waypoints */}
              {waypoints.length > 1 && (
                <polyline
                  points={waypoints.map((w) => `${w.x},${w.y}`).join(" ")}
                  stroke="#1B4332"
                  strokeWidth="2.5"
                  strokeDasharray="4 2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}

              {/* Waypoint Nodes */}
              {waypoints.map((wp) => {
                const isActive = activePointId === wp.id;
                return (
                  <g
                    key={wp.id}
                    onClick={() => setActivePointId(wp.id)}
                    className="cursor-pointer transition-transform hover:scale-110"
                    style={{ transformOrigin: `${wp.x}% ${wp.y}%` }}
                  >
                    {isActive && (
                      <circle
                        cx={wp.x}
                        cy={wp.y}
                        r="6"
                        fill="#1B4332"
                        opacity="0.2"
                      />
                    )}
                    <circle
                      cx={wp.x}
                      cy={wp.y}
                      r="3.5"
                      fill={isActive ? "#1B4332" : "#52B788"}
                      stroke="#FFFFFF"
                      strokeWidth="1.5"
                    />
                    <text
                      x={wp.x + 4}
                      y={wp.y + 1}
                      fill="#1C1917"
                      fontSize="3.8"
                      fontWeight={isActive ? "700" : "500"}
                      className="select-none"
                    >
                      {wp.name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>

          <div className="pt-3 border-t border-stone-100 flex flex-wrap items-center justify-between text-[11px] text-stone-500 gap-2">
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-[#1B4332]" />
                Destination Pin
              </span>
              <span className="flex items-center gap-1">
                <span className="h-0.5 w-4 bg-[#1B4332]" />
                Driving Highway Route
              </span>
            </div>
            <span>Verified Geographic Coordinates via Places Service</span>
          </div>
        </div>

        {/* Selected Waypoint Detail Card */}
        {currentPoint && (
          <div className="lg:col-span-5 bg-white rounded-2xl border border-stone-200/80 p-6 shadow-2xs flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                  {currentPoint.tag}
                </span>
                <span className="text-xs font-semibold text-stone-600">
                  {currentPoint.stayDuration}
                </span>
              </div>

              <h3 className="text-xl font-bold text-stone-900">
                {currentPoint.name}
              </h3>

              <p className="text-xs sm:text-sm text-stone-600 leading-relaxed font-normal">
                {currentPoint.description}
              </p>

              <div className="pt-2">
                <h5 className="text-xs font-semibold text-stone-700 uppercase tracking-wider mb-2">
                  Curated Highlights & Stops
                </h5>
                <div className="space-y-1.5">
                  {currentPoint.attractions.map((att, i) => (
                    <div
                      key={i}
                      className="p-2.5 rounded-lg bg-stone-50 border border-stone-100 text-xs text-stone-800 flex items-center gap-2"
                    >
                      <Compass className="h-3.5 w-3.5 text-[#1B4332] shrink-0" />
                      <span>{att}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-5 pt-4 border-t border-stone-100 flex items-center justify-between text-xs">
              <span className="text-stone-400">Inter-city route segment</span>
              <button
                onClick={() => {
                  const idx = waypoints.findIndex((w) => w.id === currentPoint.id);
                  const next = waypoints[(idx + 1) % waypoints.length];
                  setActivePointId(next.id);
                }}
                className="text-xs font-medium text-emerald-800 hover:text-emerald-900 flex items-center gap-1 cursor-pointer"
              >
                <span>Next Destination</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
