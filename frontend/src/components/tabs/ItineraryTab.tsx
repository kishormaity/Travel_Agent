"use client";

import React, { useState } from "react";
import {
  Calendar,
  Clock,
  Car,
  Plane,
  MapPin,
  Sun,
  Sunset,
  Moon,
  ChevronRight,
  Compass,
} from "lucide-react";
import { useTripStore } from "../../store/useTripStore";

export function ItineraryTab() {
  const { trip } = useTripStore();
  const [selectedDay, setSelectedDay] = useState<number | null>(null);

  if (!trip) return null;

  const daysToShow =
    selectedDay !== null
      ? trip.itinerary.filter((d) => d.day === selectedDay)
      : trip.itinerary;

  const getTimeIcon = (time: string) => {
    switch (time) {
      case "Morning":
        return <Sun className="h-4 w-4 text-amber-500" />;
      case "Afternoon":
        return <Sunset className="h-4 w-4 text-orange-500" />;
      case "Evening":
        return <Moon className="h-4 w-4 text-indigo-500" />;
      default:
        return <Clock className="h-4 w-4 text-stone-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Day Selector Pills */}
      <div className="bg-white rounded-2xl border border-stone-200/80 p-4 shadow-2xs">
        <div className="flex items-center justify-between flex-wrap gap-2 mb-2 pb-2 border-b border-stone-100">
          <span className="text-xs font-semibold uppercase tracking-wider text-stone-500">
            Day-by-Day Schedule ({trip.itinerary.length} Days)
          </span>
          <button
            onClick={() => setSelectedDay(null)}
            className={`text-xs font-medium px-2.5 py-1 rounded-lg transition-colors ${
              selectedDay === null
                ? "bg-[#1B4332] text-white"
                : "text-stone-600 hover:bg-stone-100"
            }`}
          >
            Show All Days
          </button>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          {trip.itinerary.map((d, idx) => {
            const isSelected = selectedDay === d.day;
            return (
              <button
                key={`itinerary-filter-day-${d.day || idx}`}
                onClick={() => setSelectedDay(isSelected ? null : d.day)}
                className={`flex flex-col items-center min-w-[76px] px-3 py-2 rounded-xl border text-xs transition-all cursor-pointer ${
                  isSelected
                    ? "bg-emerald-50 border-emerald-600 text-emerald-900 font-semibold shadow-2xs"
                    : "bg-stone-50/70 border-stone-200/70 text-stone-700 hover:bg-stone-100/70"
                }`}
              >
                <span className="font-bold">Day {d.day}</span>
                <span className="text-[10px] text-stone-500 truncate max-w-[64px]">
                  {d.destination}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Day Cards List */}
      <div className="space-y-6">
        {daysToShow.map((day, idx) => (
          <div
            key={`itinerary-day-card-${day.day || idx}`}
            className="bg-white rounded-2xl border border-stone-200/80 p-5 sm:p-7 shadow-2xs space-y-5"
          >
            {/* Day Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-100 gap-2">
              <div className="flex items-center gap-3">
                <span className="h-9 w-9 rounded-xl bg-[#1B4332] text-white flex items-center justify-center font-bold text-sm shadow-xs">
                  D{day.day}
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md">
                      {day.destination}
                    </span>
                    <span className="text-xs text-stone-400">•</span>
                    <span className="text-xs text-stone-500 font-medium">
                      {day.date}
                    </span>
                  </div>
                  <h3 className="text-base sm:text-lg font-semibold text-stone-900 mt-1">
                    {day.title}
                  </h3>
                </div>
              </div>
            </div>

            {/* Narrative Summary */}
            <p className="text-sm text-stone-600 font-normal leading-relaxed">
              {day.summary}
            </p>

            {/* Inter-city Transit Banner if present */}
            {day.transit && (
              <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200/60 flex flex-wrap items-center justify-between gap-3 text-xs text-amber-900">
                <div className="flex items-center gap-2">
                  <div className="h-7 w-7 rounded-lg bg-amber-100 flex items-center justify-center text-amber-800">
                    {day.transit.mode.includes("Flight") ? (
                      <Plane className="h-4 w-4" />
                    ) : (
                      <Car className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <span className="font-semibold text-amber-950">
                      Transit Segment: {day.transit.from} → {day.transit.to}
                    </span>
                    <span className="block text-[11px] text-amber-800">
                      {day.transit.mode}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs font-medium">
                  {day.transit.distance && (
                    <span>Distance: {day.transit.distance}</span>
                  )}
                  <span>Est. Duration: {day.transit.duration}</span>
                </div>
              </div>
            )}

            {/* Activity Milestones (Morning, Afternoon, Evening) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-2">
              {day.activities.map((act, idx) => (
                <div
                  key={`activity-${day.day || 0}-${act.time}-${idx}`}
                  className="p-4 rounded-xl bg-stone-50/60 border border-stone-200/60 hover:bg-stone-50 transition-colors flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-700">
                        {getTimeIcon(act.time)}
                        {act.time}
                      </span>
                      {act.tag && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-stone-200/70 text-stone-700 font-medium">
                          {act.tag}
                        </span>
                      )}
                    </div>
                    <h5 className="text-sm font-semibold text-stone-900 mb-1.5 leading-snug">
                      {act.title}
                    </h5>
                    <p className="text-xs text-stone-600 leading-relaxed font-normal">
                      {act.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

