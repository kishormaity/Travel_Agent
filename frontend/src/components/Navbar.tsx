"use client";

import React, { useState } from "react";
import { Compass, Calendar, Bookmark, MapPin, User, Check, ExternalLink } from "lucide-react";
import { useTripStore } from "../store/useTripStore";

export function Navbar() {
  const { setActiveTab } = useTripStore();
  const [showMyTrips, setShowMyTrips] = useState(false);

  return (
    <header className="sticky top-0 z-40 w-full bg-[#FAF9F6]/90 backdrop-blur-md border-b border-stone-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-[#1B4332] text-white flex items-center justify-center shadow-sm">
            <Compass className="h-5 w-5" />
          </div>
          <div>
            <span className="text-lg font-semibold tracking-tight text-stone-900">
              Wayfarer
            </span>
            <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-[11px] font-medium tracking-wide uppercase bg-emerald-50 text-emerald-800 border border-emerald-200/60 rounded-full">
              AI Travel Planner
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => {
              setActiveTab("overview");
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-stone-900 bg-white border border-stone-200 rounded-lg shadow-2xs hover:bg-stone-50 transition-colors"
          >
            <Calendar className="h-4 w-4 text-[#1B4332]" />
            <span>Plan Trip</span>
          </button>

          <div className="relative">
            <button
              onClick={() => setShowMyTrips(!showMyTrips)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-100/70 rounded-lg transition-colors"
            >
              <Bookmark className="h-4 w-4" />
              <span>My Trips</span>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-600"></span>
            </button>

            {/* My Trips Quick Dropdown */}
            {showMyTrips && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-stone-200 p-3 z-50">
                <div className="flex items-center justify-between pb-2 border-b border-stone-100">
                  <span className="text-xs font-semibold text-stone-500 uppercase tracking-wider">
                    Recent Saved Plans
                  </span>
                  <span className="text-xs text-emerald-700 font-medium">1 Active</span>
                </div>
                <div className="mt-2 space-y-2">
                  <div className="p-2.5 rounded-lg bg-stone-50 hover:bg-stone-100/80 cursor-pointer border border-stone-200/60 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-xs text-stone-900">
                        Kerala: Kochi, Munnar & Alleppey
                      </span>
                      <span className="text-[10px] bg-emerald-100 text-emerald-800 font-medium px-1.5 py-0.5 rounded">
                        7 Days
                      </span>
                    </div>
                    <div className="text-[11px] text-stone-500 mt-1 flex items-center gap-2">
                      <span>10–17 Jan 2027</span>
                      <span>•</span>
                      <span>3 Adults</span>
                      <span>•</span>
                      <span className="text-emerald-700 font-medium">₹88,700</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <button
            onClick={() => {
              const el = document.getElementById("trip-workspace");
              if (el) el.scrollIntoView({ behavior: "smooth" });
              setActiveTab("itinerary");
            }}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-100/70 rounded-lg transition-colors cursor-pointer"
          >
            <Compass className="h-4 w-4" />
            <span>Itinerary</span>
          </button>

          {/* User Profile Avatar */}
          <div className="ml-2 pl-2 border-l border-stone-200 flex items-center">
            <div className="h-8 w-8 rounded-full bg-stone-200 flex items-center justify-center text-stone-700 text-xs font-semibold ring-2 ring-white">
              <User className="h-4 w-4 text-stone-600" />
            </div>
          </div>
        </nav>
      </div>
    </header>
  );
}

