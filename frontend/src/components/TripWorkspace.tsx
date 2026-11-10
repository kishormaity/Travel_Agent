"use client";

import React from "react";
import { AlertTriangle } from "lucide-react";
import { useTripStore } from "../store/useTripStore";
import { TripHeader } from "./TripHeader";
import { WorkspaceTabs } from "./WorkspaceTabs";
import { FormattedOutputViewer } from "./FormattedOutputViewer";
import { FlightsTab } from "./tabs/FlightsTab";
import { HotelsTab } from "./tabs/HotelsTab";
import { ItineraryTab } from "./tabs/ItineraryTab";
import { BudgetTab } from "./tabs/BudgetTab";

export function TripWorkspace() {
  const { trip, activeTab, hasGeneratedTrip, errorMessage, clearError } = useTripStore();

  if (errorMessage && !hasGeneratedTrip) {
    return (
      <section id="trip-workspace" className="py-12 bg-[#FAF9F6]">
        <div className="max-w-2xl mx-auto px-4">
          <div className="bg-white rounded-2xl border border-red-200/90 p-8 text-center shadow-xs">
            <div className="w-14 h-14 rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center text-red-600 mx-auto mb-4">
              <AlertTriangle className="h-7 w-7 text-red-600" />
            </div>
            <h3 className="text-xl font-bold text-stone-900 tracking-tight mb-2">
              No Data Returned From Backend
            </h3>
            <p className="text-sm text-stone-600 mb-6 max-w-md mx-auto leading-relaxed">
              {errorMessage}
            </p>
            <button
              onClick={clearError}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-[#1B4332] hover:bg-[#2D6A4F] transition-colors shadow-2xs cursor-pointer"
            >
              Dismiss and Try Again
            </button>
          </div>
        </div>
      </section>
    );
  }

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
