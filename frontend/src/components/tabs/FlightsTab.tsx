"use client";

import React, { useState, useMemo } from "react";
import {
  Plane,
  Luggage,
  ExternalLink,
  Calendar,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Tag,
  ChevronDown,
  ChevronUp,
  ArrowLeftRight,
  Compass,
  ArrowLeft,
} from "lucide-react";
import { useTripStore } from "../../store/useTripStore";
import { FlightOption } from "../../types/trip";

type FlightViewMode = "best_deal" | "all_going" | "all_returning";

export function FlightsTab() {
  const { trip } = useTripStore();
  const [viewMode, setViewMode] = useState<FlightViewMode>("best_deal");
  const [isOneWayExpanded, setIsOneWayExpanded] = useState(false);

  const travelersCount = trip?.travelers?.count || 1;
  const travelersLabel = trip?.travelers?.label || "1 Adult";

  // Separate Outbound (Going) and Return (Returning) flights
  const { sortedOutbound, sortedReturn, isRoundTrip } = useMemo(() => {
    if (!trip) return { sortedOutbound: [], sortedReturn: [], isRoundTrip: false };

    const rawAll = trip.flights || [];
    const rawOutbound = trip.outbound_flights && trip.outbound_flights.length > 0
      ? trip.outbound_flights
      : rawAll.filter((f) => f.direction !== "return");

    const rawReturn = trip.return_flights && trip.return_flights.length > 0
      ? trip.return_flights
      : rawAll.filter((f) => f.direction === "return");

    const sortByPrice = (list: FlightOption[]) =>
      [...list].sort((a, b) => {
        const pA = typeof a.price === "number" ? a.price : parseFloat(String(a.price || 0)) || 0;
        const pB = typeof b.price === "number" ? b.price : parseFloat(String(b.price || 0)) || 0;
        return pA - pB;
      });

    const sOut = sortByPrice(rawOutbound);
    const sRet = sortByPrice(rawReturn);

    const hasReturn = sRet.length > 0 || trip.trip_type === "roundtrip" || Boolean(trip.travel_dates?.end && trip.travel_dates.end !== trip.travel_dates.start);

    return {
      sortedOutbound: sOut,
      sortedReturn: sRet,
      isRoundTrip: hasReturn,
    };
  }, [trip]);

  if (!trip) return null;

  if (sortedOutbound.length === 0 && sortedReturn.length === 0) {
    const originLabel = trip.routes?.[0]?.origin || "Origin";
    const destLabel = trip.destinations?.[0] || trip.routes?.[0]?.destination || "Destination";
    return (
      <div className="bg-white rounded-2xl border border-stone-200/90 p-8 sm:p-12 text-center shadow-2xs">
        <div className="mx-auto w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200/80 flex items-center justify-center text-amber-700 mb-4 shadow-2xs">
          <Plane className="h-8 w-8 text-amber-700" />
        </div>
        <h3 className="text-xl sm:text-2xl font-extrabold text-stone-900 tracking-tight mb-2">
          No Flights Found Matching Your Exact Criteria
        </h3>
        <p className="text-sm text-stone-600 max-w-xl mx-auto mb-6 leading-relaxed">
          No live flights matched the requested route ({originLabel} ➔ {destLabel}), cabin class, or stop preferences.
          Direct non-stop service on many domestic routes is operated exclusively in <strong>Economy class</strong> (e.g. IndiGo, Akasa Air, Air India Express).
        </p>
        <div className="inline-flex flex-col sm:flex-row items-center gap-3 p-4 bg-emerald-50/90 rounded-xl border border-emerald-200 text-xs sm:text-sm text-emerald-950 font-medium max-w-xl mx-auto text-left shadow-2xs">
          <span className="font-bold text-emerald-800 shrink-0">💡 Recommendation:</span>
          <span>Please check <strong>Economy class</strong> for direct non-stop flights, or select <strong>Any Stops</strong> to explore connecting premium itineraries.</span>
        </div>
      </div>
    );
  }

  const lowestGoing = sortedOutbound.length > 0 ? sortedOutbound[0] : null;
  const lowestReturn = sortedReturn.length > 0 ? sortedReturn[0] : null;

  const goingOrigin = lowestGoing?.origin || sortedOutbound[0]?.origin || "CCU";
  const goingDest = lowestGoing?.destination || sortedOutbound[0]?.destination || "BLR";
  const goingDate = lowestGoing?.departure_date || trip.travel_dates?.start || "";

  const returnOrigin = lowestReturn?.origin || goingDest;
  const returnDest = lowestReturn?.destination || goingOrigin;
  const returnDate = lowestReturn?.departure_date || trip.travel_dates?.end || "";

  const combinedLowestPrice =
    (lowestGoing?.price || 0) + (isRoundTrip && lowestReturn ? lowestReturn.price : 0);

  // Render a standardized individual flight box card
  const renderFlightBox = (
    flight: FlightOption,
    options: {
      highlightLabel?: string;
      isCheapest?: boolean;
      journeyBadge?: string;
    },
    keyPrefix?: string | number
  ) => {
    const isCheapest = options.isCheapest || flight.is_lowest_price;
    const originAirport = flight.origin || goingOrigin;
    const destAirport = flight.destination || goingDest;
    const departureDate = flight.departure_date || (flight.direction === "return" ? returnDate : goingDate);
    const arrivalDate = flight.arrival_date || departureDate;
    const depTime = flight.departure_time || "00:00";
    const arrTime = flight.arrival_time || "00:00";
    const stopsCount = typeof flight.stops === "number" ? flight.stops : 0;
    const isNonStop = stopsCount === 0 || flight.is_direct === true;
    const durationStr = flight.duration_formatted || flight.duration || "2h 40m";
    const flightNo = flight.flight_number || (flight.flight_numbers && flight.flight_numbers.join(", ")) || "Direct Flight";
    const bookingUrl = flight.booking_url || `https://www.google.com/travel/flights?q=Flights%20from%20${originAirport}%20to%20${destAirport}`;
    const perPersonPrice = flight.price || 0;
    const totalPrice = perPersonPrice * travelersCount;

    const elementKey =
      keyPrefix !== undefined
        ? `flight-${keyPrefix}-${flight.id || flight.flight_number || "fl"}-${flight.departure_time || ""}`
        : flight.id
        ? `flight-${flight.id}`
        : `flight-${flight.flight_number || "fl"}-${flight.departure_time || ""}-${flight.price || ""}`;

    return (
      <div
        key={elementKey}
        className={`rounded-2xl border transition-all duration-200 relative overflow-hidden bg-white ${
          isCheapest
            ? "border-emerald-600 ring-2 ring-emerald-500/20 shadow-md"
            : "border-stone-200/90 shadow-2xs hover:border-stone-300 hover:shadow-xs"
        }`}
      >
        {/* Highlight Banner Ribbon */}
        {options.highlightLabel && (
          <div className="bg-gradient-to-r from-[#1B4332] to-[#2D6A4F] text-white text-[11px] font-bold px-4 py-1.5 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-emerald-300" />
              <span>{options.highlightLabel}</span>
            </div>
            <span className="text-emerald-200 text-[10px] tracking-wide uppercase">
              Best Live Match
            </span>
          </div>
        )}

        <div className="p-5 sm:p-6 space-y-5">
          {/* Header Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-stone-100 gap-4">
            <div className="flex items-center gap-3.5">
              <div
                className={`h-11 w-11 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                  isCheapest ? "bg-emerald-100 text-[#1B4332]" : "bg-stone-100 text-stone-800"
                }`}
              >
                <Plane className="h-5 w-5 text-[#1B4332]" />
              </div>

              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-base sm:text-lg font-extrabold text-stone-900">
                    {flight.airline}
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-stone-100 text-stone-700 border border-stone-200">
                    {flightNo}
                  </span>
                  {options.journeyBadge && (
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-stone-100 text-stone-700 border border-stone-200">
                      {options.journeyBadge}
                    </span>
                  )}
                  {isCheapest && (
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-900 border border-emerald-300 flex items-center gap-1">
                      <Tag className="h-3 w-3 text-emerald-700" />
                      Lowest Fare
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 text-xs text-stone-500 mt-1">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    {isNonStop ? "Non-Stop Direct" : `${stopsCount} Stop(s)`}
                  </span>
                  <span>•</span>
                  <span>{flight.cabin_baggage || "Cabin Bag: 7 kg included"}</span>
                </div>
              </div>
            </div>

            {/* Price Box */}
            <div className="sm:text-right">
              <span className="text-[11px] font-semibold text-stone-400 block uppercase tracking-wider">
                Published Live Fare
              </span>
              <div className="text-2xl sm:text-3xl font-black text-[#1B4332]">
                ₹{perPersonPrice.toLocaleString()}
                <span className="text-xs font-normal text-stone-500 ml-1">/ person</span>
              </div>
              {travelersCount > 1 && (
                <span className="text-xs text-stone-500 block mt-0.5">
                  Total: <strong className="text-stone-800">₹{totalPrice.toLocaleString()}</strong> for {travelersLabel}
                </span>
              )}
            </div>
          </div>

          {/* Schedule & Duration Visual Box */}
          <div className="p-4 sm:p-5 rounded-xl bg-stone-50/90 border border-stone-200/80">
            <div className="flex items-center justify-between text-xs font-semibold text-stone-500 mb-3">
              <span className="flex items-center gap-1.5 text-stone-800">
                <Calendar className="h-3.5 w-3.5 text-[#1B4332]" />
                Flight Date: {departureDate}
              </span>
              <span className={isNonStop ? "text-emerald-800 font-bold" : "text-amber-800 font-bold"}>
                {isNonStop ? "Direct Non-Stop" : `${stopsCount} Layover Stop(s)`}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 items-center gap-4 text-center sm:text-left">
              {/* Departure */}
              <div>
                <span className="text-2xl font-black text-stone-900 block leading-tight">
                  {depTime}
                </span>
                <span className="text-sm font-bold text-stone-800 block">
                  {originAirport}
                </span>
                <span className="text-xs text-stone-500 block">
                  Departure • {departureDate}
                </span>
              </div>

              {/* Transit Timeline */}
              <div className="text-center px-2">
                <span className="text-xs font-semibold text-stone-600 inline-flex items-center gap-1 mb-1">
                  <Clock className="h-3.5 w-3.5 text-[#1B4332]" />
                  {durationStr}
                </span>
                <div className="relative flex items-center justify-center my-1">
                  <div className="w-full border-t-2 border-dashed border-stone-300" />
                  <div className="absolute h-6 w-6 rounded-full bg-white border border-stone-300 flex items-center justify-center shadow-2xs">
                    <Plane className="h-3 w-3 text-[#1B4332]" />
                  </div>
                </div>
                <span className="text-[11px] font-medium text-stone-500 block">
                  {originAirport} ➔ {destAirport}
                </span>
              </div>

              {/* Arrival */}
              <div className="sm:text-right">
                <span className="text-2xl font-black text-stone-900 block leading-tight">
                  {arrTime}
                </span>
                <span className="text-sm font-bold text-stone-800 block">
                  {destAirport}
                </span>
                <span className="text-xs text-stone-500 block">
                  Arrival • {arrivalDate}
                </span>
              </div>
            </div>
          </div>

          {/* Footer & Direct Google Flights Link */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="flex items-center gap-2 text-xs text-stone-600">
              <Luggage className="h-4 w-4 text-stone-400 shrink-0" />
              <span>
                {flight.baggage || "Cabin bag included (up to 7kg). Check-in bag subject to airline fare tier."}
              </span>
            </div>

            <a
              href={bookingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={`inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm transition-all cursor-pointer shadow-2xs ${
                isCheapest
                  ? "bg-[#1B4332] hover:bg-[#2D6A4F] text-white shadow-emerald-900/10 hover:shadow-md"
                  : "bg-stone-900 hover:bg-stone-800 text-white"
              }`}
            >
              <span>Book on Google Flights</span>
              <ExternalLink className="h-4 w-4 text-emerald-200" />
            </a>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner Overview */}
      <div className="bg-white rounded-2xl border border-stone-200/90 p-5 sm:p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1.5">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-[#1B4332] text-white">
                {isRoundTrip ? (
                  <>
                    <ArrowLeftRight className="h-3.5 w-3.5 text-emerald-300" />
                    <span>Round-Trip ({goingOrigin} ⇄ {goingDest})</span>
                  </>
                ) : (
                  <>
                    <Plane className="h-3.5 w-3.5 text-emerald-300" />
                    <span>One-Way ({goingOrigin} ➔ {goingDest})</span>
                  </>
                )}
              </span>

              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-900 border border-emerald-200">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-700" />
                Google Flights Live Rates
              </span>

              {goingDate && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-stone-100 text-stone-700">
                  <Calendar className="h-3 w-3 text-stone-500" />
                  Depart: {goingDate}
                </span>
              )}

              {isRoundTrip && returnDate && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-stone-100 text-stone-700">
                  <Calendar className="h-3 w-3 text-stone-500" />
                  Return: {returnDate}
                </span>
              )}
            </div>

            <h2 className="text-lg sm:text-xl font-extrabold text-stone-900 tracking-tight">
              {isRoundTrip ? "Round-Trip Flight Intelligence" : "One-Way Flight Intelligence"}
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              {isRoundTrip
                ? `Individually executed one-way searches for both going (${sortedOutbound.length} options) and returning (${sortedReturn.length} options). The cheapest combination is highlighted below.`
                : `Executed verified flight search for your outbound journey with ${sortedOutbound.length} available flights.`}
            </p>
          </div>

          {/* Pricing Highlight Pill */}
          <div className="flex items-center gap-3 self-start md:self-auto shrink-0">
            <div className="text-right">
              <span className="text-[11px] font-semibold text-stone-500 block uppercase tracking-wider">
                {isRoundTrip ? "Cheapest Round-Trip Total" : "Lowest Going Fare"}
              </span>
              <span className="text-2xl font-black text-[#1B4332]">
                ₹{combinedLowestPrice.toLocaleString()}
                <span className="text-xs font-normal text-stone-500 ml-1">/ person</span>
              </span>
              {isRoundTrip && lowestGoing && lowestReturn && (
                <span className="text-[11px] text-stone-500 block">
                  ₹{lowestGoing.price.toLocaleString()} (Going) + ₹{lowestReturn.price.toLocaleString()} (Return)
                </span>
              )}
            </div>
          </div>
        </div>

        {/* View Mode Switcher Pills (If Round-Trip) */}
        {isRoundTrip && sortedReturn.length > 0 && (
          <div className="mt-5 pt-4 border-t border-stone-100 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center p-1 bg-stone-100/90 rounded-xl border border-stone-200/80">
              <button
                type="button"
                onClick={() => setViewMode("best_deal")}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  viewMode === "best_deal"
                    ? "bg-[#1B4332] text-white shadow-xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-white/60"
                }`}
              >
                <Sparkles className="h-3.5 w-3.5 text-emerald-300" />
                <span>Best Value Round-Trip Deal</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode("all_going")}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  viewMode === "all_going"
                    ? "bg-[#1B4332] text-white shadow-xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-white/60"
                }`}
              >
                <Plane className="h-3.5 w-3.5" />
                <span>All Going Flights ({sortedOutbound.length})</span>
              </button>

              <button
                type="button"
                onClick={() => setViewMode("all_returning")}
                className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                  viewMode === "all_returning"
                    ? "bg-[#1B4332] text-white shadow-xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-white/60"
                }`}
              >
                <ArrowRight className="h-3.5 w-3.5" />
                <span>All Returning Flights ({sortedReturn.length})</span>
              </button>
            </div>

            {viewMode !== "best_deal" && (
              <button
                type="button"
                onClick={() => setViewMode("best_deal")}
                className="inline-flex items-center gap-1.5 text-xs font-bold text-[#1B4332] hover:underline cursor-pointer"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                <span>Back to Best Value Deal</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* ROUND-TRIP MODE VIEWS */}
      {isRoundTrip && sortedReturn.length > 0 ? (
        <>
          {/* 1. Best Deal View (Cheapest Going + Cheapest Returning) */}
          {viewMode === "best_deal" && (
            <div className="space-y-6">
              {/* GOING LEG (OUTBOUND) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-6 w-6 rounded-full bg-[#1B4332] text-white flex items-center justify-center text-xs font-bold">
                      1
                    </span>
                    <h3 className="text-base sm:text-lg font-extrabold text-stone-900">
                      Cheapest Flight for Going: {goingOrigin} ➔ {goingDest}
                    </h3>
                  </div>
                  <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                    Depart: {goingDate}
                  </span>
                </div>

                {lowestGoing &&
                  renderFlightBox(
                    lowestGoing,
                    {
                      highlightLabel: "BEST CHEAPEST FLIGHT FOR GOING (OUTBOUND)",
                      isCheapest: true,
                      journeyBadge: "Going Leg",
                    },
                    "best-deal-going"
                  )}

                {/* Option to view all going flights */}
                {sortedOutbound.length > 1 && (
                  <div className="pt-1 text-center sm:text-left">
                    <button
                      type="button"
                      onClick={() => setViewMode("all_going")}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-white border border-stone-300 text-stone-800 hover:bg-stone-50 hover:border-[#1B4332] hover:text-[#1B4332] shadow-2xs transition-all cursor-pointer"
                    >
                      <Plane className="h-3.5 w-3.5 text-[#1B4332]" />
                      <span>
                        Show All {sortedOutbound.length} Going Flights (Fares from ₹{lowestGoing?.price.toLocaleString()})
                      </span>
                      <ChevronDown className="h-3.5 w-3.5 text-stone-400" />
                    </button>
                  </div>
                )}
              </div>

              {/* RETURNING LEG (INBOUND) */}
              <div className="space-y-3 pt-4 border-t border-stone-200/80">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-6 w-6 rounded-full bg-[#1B4332] text-white flex items-center justify-center text-xs font-bold">
                      2
                    </span>
                    <h3 className="text-base sm:text-lg font-extrabold text-stone-900">
                      Cheapest Flight for Returning: {returnOrigin} ➔ {returnDest}
                    </h3>
                  </div>
                  <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                    Return: {returnDate}
                  </span>
                </div>

                {lowestReturn &&
                  renderFlightBox(
                    lowestReturn,
                    {
                      highlightLabel: "BEST CHEAPEST FLIGHT FOR RETURNING (INBOUND)",
                      isCheapest: true,
                      journeyBadge: "Returning Leg",
                    },
                    "best-deal-return"
                  )}

                {/* Option to view all returning flights */}
                {sortedReturn.length > 1 && (
                  <div className="pt-1 text-center sm:text-left">
                    <button
                      type="button"
                      onClick={() => setViewMode("all_returning")}
                      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-white border border-stone-300 text-stone-800 hover:bg-stone-50 hover:border-[#1B4332] hover:text-[#1B4332] shadow-2xs transition-all cursor-pointer"
                    >
                      <ArrowRight className="h-3.5 w-3.5 text-[#1B4332]" />
                      <span>
                        Show All {sortedReturn.length} Returning Flights (Fares from ₹{lowestReturn?.price.toLocaleString()})
                      </span>
                      <ChevronDown className="h-3.5 w-3.5 text-stone-400" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 2. All Going Flights View */}
          {viewMode === "all_going" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-50/70 border border-emerald-200">
                <div>
                  <h3 className="text-sm sm:text-base font-extrabold text-emerald-950">
                    All Available Flights for Going ({goingOrigin} ➔ {goingDest})
                  </h3>
                  <p className="text-xs text-emerald-800">
                    Showing all {sortedOutbound.length} going options sorted in ascending order of price. Depart date: {goingDate}.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setViewMode("best_deal")}
                  className="px-3 py-1.5 rounded-lg bg-white border border-emerald-300 text-xs font-bold text-[#1B4332] hover:bg-emerald-50 transition-all cursor-pointer shrink-0"
                >
                  ← Back to Best Deal
                </button>
              </div>

              <div className="space-y-4">
                {sortedOutbound.map((flight, idx) =>
                  renderFlightBox(
                    flight,
                    {
                      highlightLabel: idx === 0 ? "CHEAPEST GOING FLIGHT" : undefined,
                      isCheapest: idx === 0,
                      journeyBadge: `Going Option #${idx + 1}`,
                    },
                    `all-going-${idx}`
                  )
                )}
              </div>
            </div>
          )}

          {/* 3. All Returning Flights View */}
          {viewMode === "all_returning" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-50/70 border border-emerald-200">
                <div>
                  <h3 className="text-sm sm:text-base font-extrabold text-emerald-950">
                    All Available Flights for Returning ({returnOrigin} ➔ {returnDest})
                  </h3>
                  <p className="text-xs text-emerald-800">
                    Showing all {sortedReturn.length} return options sorted in ascending order of price. Return date: {returnDate}.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setViewMode("best_deal")}
                  className="px-3 py-1.5 rounded-lg bg-white border border-emerald-300 text-xs font-bold text-[#1B4332] hover:bg-emerald-50 transition-all cursor-pointer shrink-0"
                >
                  ← Back to Best Deal
                </button>
              </div>

              <div className="space-y-4">
                {sortedReturn.map((flight, idx) =>
                  renderFlightBox(
                    flight,
                    {
                      highlightLabel: idx === 0 ? "CHEAPEST RETURNING FLIGHT" : undefined,
                      isCheapest: idx === 0,
                      journeyBadge: `Return Option #${idx + 1}`,
                    },
                    `all-returning-${idx}`
                  )
                )}
              </div>
            </div>
          )}
        </>
      ) : (
        /* ONE-WAY TRIP VIEW */
        <div className="space-y-5">
          <div className="space-y-4">
            {(isOneWayExpanded ? sortedOutbound : sortedOutbound.slice(0, 1)).map((flight, idx) =>
              renderFlightBox(
                flight,
                {
                  highlightLabel: idx === 0 ? "CHEAPEST AVAILABLE FLIGHT • BEST VALUE" : undefined,
                  isCheapest: idx === 0,
                  journeyBadge: "One-Way Flight",
                },
                `oneway-${idx}`
              )
            )}
          </div>

          {/* Expand/Collapse Button for One-Way */}
          {sortedOutbound.length > 1 && (
            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={() => setIsOneWayExpanded(!isOneWayExpanded)}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-bold text-sm bg-white border-2 border-[#1B4332] text-[#1B4332] hover:bg-[#1B4332] hover:text-white transition-all duration-200 shadow-xs cursor-pointer group"
              >
                {isOneWayExpanded ? (
                  <>
                    <ChevronUp className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" />
                    <span>Show Less (Lowest Flight Only)</span>
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 transition-transform group-hover:translate-y-0.5" />
                    <span>
                      Show All {sortedOutbound.length} Flights (Fares from ₹{lowestGoing?.price.toLocaleString()})
                    </span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
