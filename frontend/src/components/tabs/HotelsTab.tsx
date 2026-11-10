"use client";

import React, { useMemo } from "react";
import {
  Building2,
  Star,
  MapPin,
  Calendar,
  Users,
  ExternalLink,
  Tag,
  Clock,
  Compass,
  CheckCircle2,
  Navigation,
} from "lucide-react";
import { useTripStore } from "../../store/useTripStore";
import { HotelOption } from "../../types/trip";

export function HotelsTab() {
  const { trip } = useTripStore();

  const getHotelRate = (h: HotelOption): number => {
    const val =
      h.rate_per_night ??
      h.price_per_night ??
      h.total_price ??
      h.total_rate;
    if (typeof val === "number" && val > 0) return val;
    if (typeof val === "string") {
      const num = parseFloat(val.replace(/[^\d.]/g, ""));
      if (!isNaN(num) && num > 0) return num;
    }
    return Number.POSITIVE_INFINITY;
  };

  const getHotelTotal = (h: HotelOption): number | null => {
    const val = h.total_price ?? h.total_rate;
    if (typeof val === "number" && val > 0) return val;
    if (typeof val === "string") {
      const num = parseFloat(val.replace(/[^\d.]/g, ""));
      if (!isNaN(num) && num > 0) return num;
    }
    return null;
  };

  const { sortedHotels, lowestRate } = useMemo(() => {
    if (!trip || !trip.hotels) return { sortedHotels: [], lowestRate: null };

    // Sort ascending by price (lowest on top)
    const sorted = [...trip.hotels].sort(
      (a, b) => getHotelRate(a) - getHotelRate(b)
    );

    const validRates = sorted
      .map((h) => getHotelRate(h))
      .filter((r) => r < Number.POSITIVE_INFINITY);

    const minRate = validRates.length > 0 ? Math.min(...validRates) : null;

    return {
      sortedHotels: sorted,
      lowestRate: minRate,
    };
  }, [trip]);

  if (!trip) return null;

  // Empty state if no accommodations exist
  if (!trip.hotels || trip.hotels.length === 0) {
    const dest = trip.destinations?.[0] || "your destination";
    return (
      <div className="bg-white rounded-2xl border border-stone-200/90 p-8 sm:p-12 text-center shadow-2xs">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200/80 flex items-center justify-center text-amber-700 mb-4 shadow-2xs">
          <Building2 className="h-8 w-8 text-amber-700" />
        </div>
        <h3 className="text-xl sm:text-2xl font-extrabold text-stone-900 tracking-tight mb-2">
          No Accommodations Found
        </h3>
        <p className="text-sm text-stone-600 max-w-xl mx-auto mb-6 leading-relaxed">
          No live hotel options were returned for {dest} on the requested travel
          dates.
        </p>
        <div className="inline-flex items-center gap-2 p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-950 font-medium">
          <span>💡 Recommendation: Check alternative travel dates or nearby districts.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Hotel Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedHotels.map((hotel, idx) => {
            const rate = getHotelRate(hotel);
            const total = getHotelTotal(hotel);
            const hasRate = rate < Number.POSITIVE_INFINITY;
            const isLowest =
              hotel.is_lowest_price ||
              (hasRate && lowestRate !== null && rate === lowestRate);
            const propertyName = hotel.name || hotel.property_name || "Verified Stay";

            return (
              <div
                key={`hotel-${hotel.id || propertyName}-${idx}`}
                className={`bg-white rounded-2xl border ${
                  isLowest ? "border-emerald-300 ring-1 ring-emerald-300" : "border-stone-200/80"
                } overflow-hidden shadow-2xs hover:shadow-md transition-all flex flex-col justify-between`}
              >
                <div>
                  {/* Top Image & Badges */}
                  <div className="relative h-48 w-full bg-stone-100 overflow-hidden">
                    {hotel.image_url ? (
                      <img
                        src={hotel.image_url}
                        alt={propertyName}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-full flex flex-col items-center justify-center bg-stone-100 text-stone-400 gap-2">
                        <Building2 className="h-10 w-10 text-stone-300" />
                        <span className="text-xs font-medium">Verified Property</span>
                      </div>
                    )}

                    {/* Location Badge */}
                    <div className="absolute top-3 left-3">
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-white/95 text-stone-900 shadow-2xs backdrop-blur-xs flex items-center gap-1">
                        <MapPin className="h-3 w-3 text-[#1B4332]" />
                        {hotel.destination_city}
                      </span>
                    </div>

                    {/* Top Right Badges: Lowest Rate & Rating */}
                    <div className="absolute top-3 right-3 flex flex-col items-end gap-1.5">
                      {isLowest && (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-600 text-white shadow-2xs flex items-center gap-1">
                          <Tag className="h-3 w-3" />
                          Lowest Rate
                        </span>
                      )}

                      {hotel.rating != null && (
                        <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[#1B4332] text-white shadow-2xs flex items-center gap-1">
                          <Star className="h-3 w-3 fill-amber-300 text-amber-300" />
                          {hotel.rating}{" "}
                          {hotel.reviews != null || hotel.reviews_count != null ? (
                            <span className="text-[10px] text-emerald-200 font-normal">
                              ({hotel.reviews ?? hotel.reviews_count})
                            </span>
                          ) : null}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Body Details */}
                  <div className="p-5 space-y-3">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        {hotel.hotel_class != null && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200">
                            {hotel.hotel_class}★ Hotel
                          </span>
                        )}
                        {hotel.property_type && (
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-stone-100 text-stone-700">
                            {hotel.property_type}
                          </span>
                        )}
                        {hotel.location_rating != null && (
                          <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-100 flex items-center gap-0.5">
                            <Navigation className="h-2.5 w-2.5" />
                            Location {hotel.location_rating}/5
                          </span>
                        )}
                      </div>

                      <h4 className="text-base font-bold text-stone-900 leading-snug">
                        {propertyName}
                      </h4>
                    </div>

                    {hotel.address && (
                      <p className="text-xs text-stone-500 line-clamp-1 flex items-center gap-1">
                        <MapPin className="h-3.5 w-3.5 shrink-0 text-stone-400" />
                        <span>{hotel.address}</span>
                      </p>
                    )}

                    {/* Dates & Times */}
                    {(hotel.check_in_date || hotel.nights != null || hotel.check_in_time) && (
                      <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-100 text-xs text-stone-600 space-y-1">
                        {hotel.check_in_date && (
                          <div className="flex items-center justify-between">
                            <span className="text-stone-400">Duration:</span>
                            <span className="font-semibold text-stone-900">
                              {hotel.nights != null ? `${hotel.nights} Nights (` : ""}
                              {hotel.check_in_date}
                              {hotel.check_out_date ? ` – ${hotel.check_out_date}` : ""}
                              {hotel.nights != null ? ")" : ""}
                            </span>
                          </div>
                        )}

                        {(hotel.check_in_time || hotel.check_out_time) && (
                          <div className="flex items-center justify-between pt-1 border-t border-stone-200/50 text-[11px]">
                            {hotel.check_in_time && (
                              <span>
                                In: <strong className="text-stone-700">{hotel.check_in_time}</strong>
                              </span>
                            )}
                            {hotel.check_out_time && (
                              <span>
                                Out: <strong className="text-stone-700">{hotel.check_out_time}</strong>
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Room Guidance */}
                    {(hotel.room_guidance || hotel.recommended_rooms) && (
                      <div className="p-2.5 rounded-xl bg-emerald-50/60 border border-emerald-100 text-xs text-emerald-950">
                        <div className="flex items-center gap-1 font-semibold text-emerald-900 mb-0.5">
                          <Users className="h-3 w-3 text-emerald-700" />
                          <span>{hotel.recommended_rooms || "Room & Guest Details"}</span>
                        </div>
                        {hotel.room_guidance && (
                          <p className="text-[11px] text-emerald-800 leading-relaxed">
                            {hotel.room_guidance}
                          </p>
                        )}
                      </div>
                    )}

                    {/* Nearby Places / Transit */}
                    {hotel.nearby_places && hotel.nearby_places.length > 0 && (
                      <div className="pt-1">
                        <span className="text-[10px] font-semibold text-stone-400 block mb-1">
                          Nearby Landmarks & Transit:
                        </span>
                        <div className="space-y-1">
                          {hotel.nearby_places.slice(0, 2).map((place, pIdx) => {
                            const transitInfo = place.transportations?.[0];
                            return (
                              <div
                                key={`nearby-${idx}-${pIdx}`}
                                className="flex items-center justify-between text-[11px] text-stone-600 bg-stone-50/80 px-2 py-1 rounded-md border border-stone-100"
                              >
                                <span className="truncate font-medium">{place.name}</span>
                                {transitInfo && (
                                  <span className="text-[10px] text-stone-500 shrink-0 ml-1">
                                    {transitInfo.type || "Transit"}: {transitInfo.duration || "Nearby"}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Amenities */}
                    {hotel.amenities && hotel.amenities.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {hotel.amenities.slice(0, 5).map((am, amIdx) => (
                          <span
                            key={`amenity-${propertyName}-${am}-${amIdx}`}
                            className="text-[10px] px-2 py-0.5 rounded-md bg-stone-100 text-stone-600 font-medium"
                          >
                            {am}
                          </span>
                        ))}
                        {hotel.amenities.length > 5 && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-stone-50 text-stone-400 font-medium">
                            +{hotel.amenities.length - 5} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Alternative Partner Channels */}
                    {hotel.prices && hotel.prices.length > 1 && (
                      <div className="pt-1">
                        <span className="text-[10px] font-semibold text-stone-400 block mb-1">
                          Booking Channels:
                        </span>
                        <div className="flex flex-wrap gap-1">
                          {hotel.prices.slice(0, 3).map((p, pIdx) => (
                            <span
                              key={`p-ch-${idx}-${pIdx}`}
                              className="text-[10px] px-2 py-0.5 rounded bg-emerald-50/70 border border-emerald-100 text-emerald-900"
                            >
                              {p.source}: ₹{Number(p.rate_per_night || 0).toLocaleString()}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Footer with Price & Booking */}
                <div className="p-5 pt-3 border-t border-stone-100 flex items-center justify-between">
                  <div>
                    {hasRate ? (
                      <>
                        <span className="text-[11px] text-stone-400 block">
                          Nightly Rate:{" "}
                          <strong className="text-stone-800 font-bold">
                            ₹{rate.toLocaleString()}
                          </strong>
                        </span>
                        {total ? (
                          <span className="text-lg font-bold text-stone-900">
                            ₹{total.toLocaleString()}{" "}
                            {hotel.nights != null && (
                              <span className="text-xs font-normal text-stone-500">
                                ({hotel.nights} night{hotel.nights > 1 ? "s" : ""})
                              </span>
                            )}
                          </span>
                        ) : (
                          <span className="text-lg font-bold text-stone-900">
                            ₹{rate.toLocaleString()}{" "}
                            <span className="text-xs font-normal text-stone-500">
                              / night
                            </span>
                          </span>
                        )}
                      </>
                    ) : (
                      <span className="text-xs font-medium text-stone-500">
                        {hotel.pricing_notice || "Live rates on request"}
                      </span>
                    )}
                  </div>

                  <a
                    href={hotel.booking_url || "https://www.google.com/travel/hotels"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#1B4332] hover:bg-[#2D6A4F] text-white text-xs font-semibold rounded-xl transition-colors cursor-pointer shadow-2xs"
                  >
                    <span>Book Stay</span>
                    <ExternalLink className="h-3 w-3 text-emerald-200" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
    </div>
  );
}
