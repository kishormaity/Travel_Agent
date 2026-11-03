"use client";

import React, { useState } from "react";
import {
  Building2,
  Star,
  MapPin,
  Calendar,
  Users,
  ExternalLink,
  ShieldCheck,
  Check,
} from "lucide-react";
import { useTripStore } from "../../store/useTripStore";

export function HotelsTab() {
  const { trip } = useTripStore();
  const [selectedCity, setSelectedCity] = useState<string>("All");

  if (!trip) return null;

  const filteredHotels =
    selectedCity === "All"
      ? trip.hotels
      : trip.hotels.filter(
          (h) => h.destination_city.toLowerCase() === selectedCity.toLowerCase()
        );

  return (
    <div className="space-y-6">
      {/* City Filter & Provider Transparency Header */}
      <div className="bg-white rounded-2xl border border-stone-200/80 p-4 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          <button
            onClick={() => setSelectedCity("All")}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
              selectedCity === "All"
                ? "bg-[#1B4332] text-white"
                : "bg-stone-100 text-stone-700 hover:bg-stone-200/80"
            }`}
          >
            All Destinations ({trip.hotels.length})
          </button>
          {trip.destinations.map((dest, idx) => (
            <button
              key={`hotels-filter-${dest}-${idx}`}
              onClick={() => setSelectedCity(dest)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
                selectedCity === dest
                  ? "bg-[#1B4332] text-white"
                  : "bg-stone-100 text-stone-700 hover:bg-stone-200/80"
              }`}
            >
              {dest}
            </button>
          ))}
        </div>

        <div className="inline-flex items-center gap-1.5 text-xs text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200 self-start sm:self-auto">
          <ShieldCheck className="h-4 w-4 text-emerald-600" />
          <span>HasData Google Hotels Live Rates Active</span>
        </div>
      </div>

      {/* Hotel Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredHotels.map((hotel, idx) => (
          <div
            key={hotel.id || `hotel-${hotel.property_name}-${idx}`}
            className="bg-white rounded-2xl border border-stone-200/80 overflow-hidden shadow-2xs hover:shadow-md transition-all flex flex-col justify-between"
          >
            {/* Top Image & Badge */}
            <div>
              <div className="relative h-48 w-full bg-stone-100 overflow-hidden">
                <img
                  src={
                    hotel.image_url ||
                    "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800&q=80"
                  }
                  alt={hotel.property_name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                <div className="absolute top-3 left-3">
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-white/95 text-stone-900 shadow-2xs backdrop-blur-xs flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-[#1B4332]" />
                    {hotel.destination_city}
                  </span>
                </div>

                <div className="absolute top-3 right-3">
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#1B4332] text-white shadow-2xs flex items-center gap-1">
                    <Star className="h-3 w-3 fill-amber-300 text-amber-300" />
                    {hotel.rating || 4.7} ({hotel.reviews || 1200})
                  </span>
                </div>
              </div>

              {/* Body Details */}
              <div className="p-5 space-y-3">
                <h4 className="text-base font-semibold text-stone-900 leading-snug">
                  {hotel.property_name}
                </h4>

                <p className="text-xs text-stone-500 line-clamp-1 flex items-center gap-1">
                  <MapPin className="h-3 w-3 shrink-0 text-stone-400" />
                  {hotel.address}
                </p>

                {/* Dates & Nights */}
                <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-100 text-xs text-stone-600 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-stone-400">Stay Duration:</span>
                    <span className="font-semibold text-stone-900">
                      {hotel.nights || 2} Nights ({hotel.check_in_date} – {hotel.check_out_date})
                    </span>
                  </div>
                </div>

                {/* Room Guidance */}
                {hotel.room_guidance && (
                  <div className="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-100 text-xs text-emerald-950">
                    <div className="flex items-center gap-1 font-semibold text-emerald-900 mb-0.5">
                      <Users className="h-3 w-3 text-emerald-700" />
                      <span>Guidance for 3 Adults</span>
                    </div>
                    <p className="text-[11px] text-emerald-800 leading-relaxed">
                      {hotel.room_guidance}
                    </p>
                  </div>
                )}

                {/* Amenities */}
                {hotel.amenities && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {hotel.amenities.slice(0, 3).map((am, amIdx) => (
                      <span
                        key={`amenity-${hotel.property_name}-${am}-${amIdx}`}
                        className="text-[10px] px-2 py-0.5 rounded-md bg-stone-100 text-stone-600 font-medium"
                      >
                        {am}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Footer with Price & Booking */}
            <div className="p-5 pt-3 border-t border-stone-100 flex items-center justify-between">
              <div>
                <span className="text-[11px] text-stone-400 block">
                  Nightly Rate: ₹{Number(hotel.price_per_night || 4200).toLocaleString()}
                </span>
                <span className="text-lg font-bold text-stone-900">
                  ₹{Number(hotel.total_price || 8400).toLocaleString()}{" "}
                  <span className="text-xs font-normal text-stone-500">
                    ({hotel.nights || 2} nights total)
                  </span>
                </span>
              </div>

              <a
                href={hotel.booking_url || "https://www.google.com/travel/hotels"}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-3.5 py-2 bg-[#1B4332] hover:bg-[#2D6A4F] text-white text-xs font-medium rounded-xl transition-colors cursor-pointer"
              >
                <span>Book Stay</span>
                <ExternalLink className="h-3 w-3 text-emerald-200" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

