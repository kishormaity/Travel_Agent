"use client";

import React, { useState } from "react";
import {
  Calendar,
  Clock,
  Car,
  Plane,
  Sun,
  Sunset,
  Moon,
  Copy,
  Check,
  Coffee,
  LayoutList,
  FileText,
} from "lucide-react";
import { useTripStore } from "../../store/useTripStore";
import { FormattedOutputViewer } from "../FormattedOutputViewer";

export function ItineraryTab() {
  const { trip } = useTripStore();
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"cards" | "text">("cards");
  const [copied, setCopied] = useState(false);

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

  const handleCopyItinerary = () => {
    if (!navigator.clipboard) return;
    const textLines = trip.itinerary.map((d) => {
      const acts = d.activities
        .map((a) => `  - [${a.time}] ${a.title}: ${a.description}`)
        .join("\n");
      return `Day ${d.day} – ${d.date} (${d.destination})\n${d.title}\nSummary: ${d.summary}\n${acts}`;
    });
    navigator.clipboard.writeText(textLines.join("\n\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Day Selector Pills & Controls */}
      <div className="bg-white rounded-2xl border border-stone-200/80 p-4 sm:p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-700">
              Day-by-Day Schedule ({trip.itinerary.length} Days)
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/60">
              All Landmarks Covered
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle: Cards vs Markdown Report */}
            <div className="inline-flex rounded-lg border border-stone-200 bg-stone-50 p-0.5 text-xs">
              <button
                type="button"
                onClick={() => setViewMode("cards")}
                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md font-medium transition-all cursor-pointer ${
                  viewMode === "cards"
                    ? "bg-white text-stone-900 shadow-2xs font-semibold"
                    : "text-stone-600 hover:text-stone-900"
                }`}
              >
                <LayoutList className="h-3.5 w-3.5" />
                <span>Timeline Cards</span>
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
              onClick={handleCopyItinerary}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200/80 border border-stone-200 rounded-lg transition-colors cursor-pointer"
              title="Copy itinerary schedule"
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

            {viewMode === "cards" && (
              <button
                onClick={() => setSelectedDay(null)}
                className={`text-xs font-medium px-2.5 py-1.5 rounded-lg transition-colors cursor-pointer ${
                  selectedDay === null
                    ? "bg-[#1B4332] text-white"
                    : "text-stone-600 hover:bg-stone-100 border border-stone-200"
                }`}
              >
                Show All Days
              </button>
            )}
          </div>
        </div>

        {/* Day Pills Bar */}
        {viewMode === "cards" && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {trip.itinerary.map((d, idx) => {
              const isSelected = selectedDay === d.day;
              const isRestDay = d.title.toLowerCase().includes("rest");
              return (
                <button
                  key={`itinerary-filter-day-${d.day || idx}`}
                  onClick={() => setSelectedDay(isSelected ? null : d.day)}
                  className={`flex flex-col items-center min-w-[80px] px-3 py-2 rounded-xl border text-xs transition-all cursor-pointer ${
                    isSelected
                      ? "bg-emerald-50 border-emerald-600 text-emerald-900 font-semibold shadow-2xs"
                      : isRestDay
                      ? "bg-amber-50/60 border-amber-200/70 text-amber-900 hover:bg-amber-100/60"
                      : "bg-stone-50/70 border-stone-200/70 text-stone-700 hover:bg-stone-100/70"
                  }`}
                >
                  <span className="font-bold flex items-center gap-1">
                    Day {d.day}
                    {isRestDay && <Coffee className="h-3 w-3 text-amber-600" />}
                  </span>
                  <span className="text-[10px] text-stone-500 truncate max-w-[72px]">
                    {isRestDay ? "Rest Day" : d.destination}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Content Rendering: Text Mode vs Cards Mode */}
      {viewMode === "text" ? (
        <FormattedOutputViewer sectionKey="itinerary" />
      ) : (
        /* Day Cards List */
        <div className="space-y-6">
          {daysToShow.map((day, idx) => {
            const isRestDay = day.title.toLowerCase().includes("rest");

            return (
              <div
                key={`itinerary-day-card-${day.day || idx}`}
                className={`bg-white rounded-2xl border p-5 sm:p-7 shadow-2xs space-y-5 transition-all ${
                  isRestDay
                    ? "border-amber-200/80 bg-gradient-to-b from-amber-50/20 to-white"
                    : "border-stone-200/80"
                }`}
              >
                {/* Day Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-100 gap-2">
                  <div className="flex items-center gap-3">
                    <span
                      className={`h-9 w-9 rounded-xl flex items-center justify-center font-bold text-sm shadow-xs ${
                        isRestDay
                          ? "bg-amber-700 text-white"
                          : "bg-[#1B4332] text-white"
                      }`}
                    >
                      D{day.day}
                    </span>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md">
                          {day.destination}
                        </span>
                        <span className="text-xs text-stone-400">•</span>
                        <span className="text-xs text-stone-500 font-medium">
                          {day.date}
                        </span>
                        {isRestDay && (
                          <span className="text-[11px] font-semibold text-amber-800 bg-amber-100/70 border border-amber-300/60 px-2.5 py-0.5 rounded-md flex items-center gap-1">
                            <Coffee className="h-3 w-3 text-amber-600" />
                            Rest & Recovery (No Sightseeing)
                          </span>
                        )}
                        {day.weather && (
                          <span className="text-[11px] text-stone-600 bg-stone-100 px-2 py-0.5 rounded-md font-medium">
                            {day.weather.temp_range} • {day.weather.condition}
                          </span>
                        )}
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
                  {day.activities.map((act, actIdx) => {
                    const isRestAct =
                      act.tag?.toLowerCase().includes("rest") ||
                      act.tag?.toLowerCase().includes("recovery") ||
                      act.tag?.toLowerCase().includes("relaxation");

                    return (
                      <div
                        key={`activity-${day.day || 0}-${act.time}-${actIdx}`}
                        className={`p-4 rounded-xl border flex flex-col justify-between transition-colors ${
                          isRestAct
                            ? "bg-amber-50/40 border-amber-200/70 hover:bg-amber-50/70"
                            : "bg-stone-50/60 border-stone-200/60 hover:bg-stone-50"
                        }`}
                      >
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-700">
                              {getTimeIcon(act.time)}
                              {act.time}
                            </span>
                            {act.tag && (
                              <span
                                className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                                  isRestAct
                                    ? "bg-amber-100 text-amber-800 border border-amber-200"
                                    : "bg-stone-200/70 text-stone-700"
                                }`}
                              >
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
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

