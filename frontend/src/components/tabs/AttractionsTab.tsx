"use client";

import React, { useState, useMemo } from "react";
import { useTripStore } from "../../store/useTripStore";
import { AttractionItem } from "../../types/trip";

export const BENGALURU_FAMOUS_ATTRACTIONS: AttractionItem[] = [
  { name: "Bugle Rock Park", city: "Bengaluru" },
  { name: "Ashoka Pillar Monument", city: "Bengaluru" },
  { name: "Lalbagh Botanical Garden", city: "Bengaluru" },
  { name: "Sri Chamarajendra Park", city: "Bengaluru" },
  { name: "Kempegowda Tower, Bengaluru", city: "Bengaluru" },
  { name: "Jawaharlal Nehru Planetarium", city: "Bengaluru" },
  { name: "Floral Clock", city: "Bengaluru" },
  { name: "Lotus Pond - Lalbagh", city: "Bengaluru" },
  { name: "Jaya Prakash Narayana Park", city: "Bengaluru" },
  { name: "Bengaluru Palace", city: "Bengaluru" },
  { name: "Banyan Tree HSR", city: "Bengaluru" },
  { name: "Snow City Bengaluru", city: "Bengaluru" },
  { name: "Bengaluru Fort", city: "Bengaluru" },
  { name: "Tipu Sultan's Summer Palace", city: "Bengaluru" },
  { name: "Begur Fort", city: "Bengaluru" },
  { name: "Namma Bengaluru Aquarium", city: "Bengaluru" },
];

export function AttractionsTab() {
  const { trip } = useTripStore();
  const [searchQuery, setSearchQuery] = useState("");

  const destinationCity =
    trip?.destinations?.[0] ||
    trip?.destination_summary ||
    "Bengaluru";

  const isBengaluru =
    destinationCity.toLowerCase().includes("bengaluru") ||
    destinationCity.toLowerCase().includes("bangalore") ||
    destinationCity.toLowerCase().includes("blr");

  const allAttractions: AttractionItem[] = useMemo(() => {
    if (trip?.attractions && trip.attractions.length > 0) {
      return trip.attractions;
    }

    if (isBengaluru) {
      return BENGALURU_FAMOUS_ATTRACTIONS;
    }

    const rawAttractionsMd = trip?.raw_sections?.attractions || "";
    if (rawAttractionsMd) {
      const parsed: AttractionItem[] = [];
      const lines = rawAttractionsMd.split("\n");
      for (const line of lines) {
        if (!line.includes("|") || line.includes("---|---") || line.toLowerCase().includes("landmark / attraction")) {
          continue;
        }
        const cols = line.split("|").map((c) => c.trim()).filter(Boolean);
        if (cols.length >= 1) {
          parsed.push({
            name: cols[0],
            city: destinationCity,
          });
        }
      }
      if (parsed.length > 0) return parsed;
    }

    return BENGALURU_FAMOUS_ATTRACTIONS;
  }, [trip, destinationCity, isBengaluru]);

  const filteredAttractions = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return allAttractions;
    return allAttractions.filter((item) =>
      item.name.toLowerCase().includes(q)
    );
  }, [allAttractions, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-stone-200">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-stone-900">
            Famous Attractions & Landmarks in {destinationCity}
          </h2>
          <p className="text-xs text-stone-500 mt-0.5">
            {allAttractions.length} Places discovered
          </p>
        </div>

        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={`Search ${allAttractions.length} attractions...`}
          className="w-full sm:w-64 h-9 px-3 text-xs bg-white border border-stone-200 rounded-lg focus:outline-none focus:border-[#1B4332] text-stone-900"
        />
      </div>

      {/* Refined Luxury Box Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 sm:gap-5">
        {filteredAttractions.map((place, idx) => {
          const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
            `${place.name} ${place.city || destinationCity}`
          )}`;

          return (
            <div
              key={`${place.name}-${idx}`}
              className="group relative bg-white rounded-2xl border border-stone-200/80 p-5 flex flex-col justify-between hover:border-emerald-600/50 hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] hover:-translate-y-0.5 transition-all duration-200 min-h-[125px]"
            >
              {/* Subtle accent hover indicator bar at top */}
              <div className="absolute inset-x-5 top-0 h-[2px] bg-gradient-to-r from-transparent via-[#1B4332] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-full" />

              <div className="font-semibold text-stone-900 text-sm tracking-tight leading-snug group-hover:text-[#1B4332] transition-colors pr-1">
                {place.name}
              </div>

              <div className="mt-4 pt-3 border-t border-stone-100 flex items-center justify-between">
                <span className="text-[11px] font-medium text-stone-400 group-hover:text-stone-600 transition-colors">
                  Location
                </span>
                <a
                  href={mapsUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg bg-stone-50 text-stone-700 border border-stone-200/80 group-hover:bg-[#1B4332] group-hover:border-[#1B4332] group-hover:text-white transition-all duration-200 shadow-2xs"
                >
                  Google Maps
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
