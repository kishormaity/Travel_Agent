"use client";

import React from "react";
import { useTripStore } from "../store/useTripStore";
import { TripHeader } from "./TripHeader";
import { WorkspaceTabs } from "./WorkspaceTabs";
import { FormattedOutputViewer } from "./FormattedOutputViewer";
import { FlightsTab } from "./tabs/FlightsTab";
import { HotelsTab } from "./tabs/HotelsTab";
import { ItineraryTab } from "./tabs/ItineraryTab";
import { BudgetTab } from "./tabs/BudgetTab";

export function TripWorkspace() {
  const { trip, activeTab, hasGeneratedTrip } = useTripStore();

  if (!hasGeneratedTrip || !trip) return null;

  return (
    <section id="trip-workspace" className="py-8 sm:py-12 bg-[#FAF9F6]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Trip Header Card with dynamic trip key */}
        <TripHeader key={`header-${trip.trip_id}`} />

        {/* Workspace Card with Dynamic Tab Navigation */}
        <div className="bg-white rounded-2xl border border-stone-200/80 shadow-xs overflow-hidden">
          <WorkspaceTabs />

          {/* Formatted Output Area: Dedicated rich templates for Flights, Hotels, Itinerary & Budget, and clean formatted viewer for other sections */}
          <div key={`content-${trip.trip_id}-${activeTab}`} className="p-4 sm:p-6 lg:p-8 bg-[#FAF9F6]/50 min-h-[460px]">
            {activeTab === "flights" ? (
              <FlightsTab />
            ) : activeTab === "hotels" ? (
              <HotelsTab />
            ) : activeTab === "itinerary" ? (
              <ItineraryTab />
            ) : activeTab === "budget" ? (
              <BudgetTab />
            ) : (
              <FormattedOutputViewer sectionKey={activeTab} />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
