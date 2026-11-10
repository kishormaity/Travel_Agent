"use client";

import React from "react";
import {
  LayoutDashboard,
  CalendarDays,
  Plane,
  Building2,
  PieChart,
  Map,
} from "lucide-react";
import { useTripStore } from "../store/useTripStore";
import { ActiveTabType } from "../types/trip";

interface TabItem {
  id: ActiveTabType;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export function WorkspaceTabs() {
  const { activeTab, setActiveTab, trip } = useTripStore();

  const flightOrigin =
    trip?.flights?.[0]?.origin ||
    trip?.flights?.[0]?.outbound_journey?.route?.split("->")[0]?.trim() ||
    "DEL";
  const flightDest =
    trip?.flights?.[0]?.destination ||
    trip?.destinations?.[0] ||
    "COK";
  const flightBadge = `${flightOrigin} ⇄ ${flightDest}`;

  const tabs: TabItem[] = [
    { id: "overview", label: "Overview", icon: LayoutDashboard },
    {
      id: "itinerary",
      label: "Itinerary",
      icon: CalendarDays,
      badge: `${trip?.itinerary?.length || 7} Days`,
    },
    {
      id: "flights",
      label: "Flights",
      icon: Plane,
      badge: flightBadge,
    },
    {
      id: "hotels",
      label: "Hotels",
      icon: Building2,
    },
    {
      id: "budget",
      label: "Budget",
      icon: PieChart,
      badge: trip ? `${trip.budget.currency_symbol}${(trip.budget.estimated_total / 1000).toFixed(1)}k` : undefined,
    },
  ];

  return (
    <div className="w-full border-b border-stone-200 bg-white rounded-t-2xl px-2 sm:px-4">
      <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto scrollbar-none py-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all whitespace-nowrap cursor-pointer ${
                isActive
                  ? "bg-[#1B4332] text-white shadow-2xs"
                  : "text-stone-600 hover:text-stone-900 hover:bg-stone-100/70"
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? "text-emerald-200" : "text-stone-500"}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-stone-100 text-stone-600"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}
