"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  MapPin,
  Calendar,
  Users,
  IndianRupee,
  Plane,
  Sparkles,
  Loader2,
  AlertCircle,
  ChevronDown,
  Plus,
  Minus,
  Armchair,
  SlidersHorizontal,
  Check,
} from "lucide-react";
import { useTripStore } from "../store/useTripStore";

const CABIN_OPTIONS = [
  {
    id: "ECONOMY",
    label: "Economy",
    description: "Standard seating & best value fare",
    badge: "Popular",
  },
  {
    id: "PREMIUM_ECONOMY",
    label: "Premium Economy",
    description: "Extra legroom, early boarding & wider seats",
    badge: "Comfort",
  },
  {
    id: "BUSINESS",
    label: "Business Class",
    description: "Lie-flat beds, lounge access & gourmet dining",
    badge: "Luxury",
  },
  {
    id: "FIRST",
    label: "First Class",
    description: "Private suites, elite service & personal dining",
    badge: "VIP",
  },
] as const;

const STOPS_OPTIONS = [
  {
    id: "ANY",
    label: "Any Stops",
    description: "Show all direct & connecting flight routes",
    badge: "Best Fare",
  },
  {
    id: "NON_STOP",
    label: "Non-Stop Direct Only",
    description: "Direct flight with no layovers or connections",
    badge: "Fastest",
  },
  {
    id: "ONE_STOP",
    label: "Up to 1 Stop",
    description: "Maximum 1 connection layover permitted",
    badge: "Flexible",
  },
  {
    id: "TWO_PLUS_STOPS",
    label: "Up to 2+ Stops",
    description: "Multi-stop routes for budget flexibility",
    badge: "Budget",
  },
] as const;

const POPULAR_PLACES = [
  {
    name: "Goa",
    emoji: "🏖️",
    tag: "Beaches & Sunset",
    suggestedBudget: 45000,
  },
  {
    name: "Jaipur, Rajasthan",
    emoji: "🏰",
    tag: "Heritage & Palaces",
    suggestedBudget: 55000,
  },
  {
    name: "Kochi & Munnar, Kerala",
    emoji: "🌴",
    tag: "Backwaters & Tea Hills",
    suggestedBudget: 65000,
  },
  {
    name: "Manali & Shimla, Himachal",
    emoji: "🏔️",
    tag: "Snow & Adventure",
    suggestedBudget: 50000,
  },
  {
    name: "Bengaluru, Karnataka",
    emoji: "🏙️",
    tag: "Gardens & Tech City",
    suggestedBudget: 60000,
  },
  {
    name: "Srinagar & Gulmarg, Kashmir",
    emoji: "🌸",
    tag: "Valleys & Lakes",
    suggestedBudget: 75000,
  },
  {
    name: "Varanasi, Uttar Pradesh",
    emoji: "🌊",
    tag: "Spiritual Ghats",
    suggestedBudget: 35000,
  },
  {
    name: "Darjeeling & Gangtok",
    emoji: "☕",
    tag: "Tea Estates & Peaks",
    suggestedBudget: 50000,
  },
] as const;

export function HeroPlanner() {
  const { formState, updateFormState, planTrip, isLoading } = useTripStore();
  const [formError, setFormError] = useState<string | null>(null);
  const [todayStr, setTodayStr] = useState("");

  const [isTravellersOpen, setIsTravellersOpen] = useState(false);
  const [isCabinOpen, setIsCabinOpen] = useState(false);
  const [isStopsOpen, setIsStopsOpen] = useState(false);

  const travellersRef = useRef<HTMLDivElement>(null);
  const cabinRef = useRef<HTMLDivElement>(null);
  const stopsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTodayStr(new Date().toISOString().split("T")[0]);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (travellersRef.current && !travellersRef.current.contains(target)) {
        setIsTravellersOpen(false);
      }
      if (cabinRef.current && !cabinRef.current.contains(target)) {
        setIsCabinOpen(false);
      }
      if (stopsRef.current && !stopsRef.current.contains(target)) {
        setIsStopsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleStartDateChange = (val: string) => {
    setFormError(null);
    let newEnd = formState.endDate;
    let newDays = formState.days;

    if (newEnd && newEnd < val) {
      newEnd = val;
    }
    if (val && newEnd) {
      const diff = Math.round(
        (new Date(newEnd).getTime() - new Date(val).getTime()) / (1000 * 60 * 60 * 24)
      );
      newDays = Math.max(1, diff + 1);
    }

    updateFormState({
      startDate: val,
      endDate: newEnd,
      days: newDays,
      dates: newEnd ? `${val} – ${newEnd}` : val,
    });
  };

  const handleEndDateChange = (val: string) => {
    setFormError(null);
    let newDays = formState.days;
    if (formState.startDate && val) {
      const diff = Math.round(
        (new Date(val).getTime() - new Date(formState.startDate).getTime()) / (1000 * 60 * 60 * 24)
      );
      newDays = Math.max(1, diff + 1);
    }

    updateFormState({
      endDate: val,
      days: newDays,
      dates: formState.startDate ? `${formState.startDate} – ${val}` : val,
    });
  };

  const handlePassengerChange = (field: "adults" | "children" | "infants", val: number) => {
    const updated = {
      adults: field === "adults" ? val : formState.adults || 1,
      children: field === "children" ? val : formState.children || 0,
      infants: field === "infants" ? val : formState.infants || 0,
    };
    const total = updated.adults + updated.children + updated.infants;
    updateFormState({
      ...updated,
      travelers: total,
    });
  };

  const handleSelectPlace = (place: (typeof POPULAR_PLACES)[number]) => {
    setFormError(null);
    updateFormState({
      destination: place.name,
      budget: formState.budget || place.suggestedBudget,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // 1. Validate Origin (Required)
    if (!formState.origin || !formState.origin.trim()) {
      setFormError("Origin city or airport is required.");
      return;
    }

    // 2. Validate Destination (Required)
    if (!formState.destination || !formState.destination.trim()) {
      setFormError("Destination is required. Please enter a city or pick from popular places.");
      return;
    }

    // 3. Validate Going Date (Required)
    if (!formState.startDate) {
      setFormError("Going (departure) date is required.");
      return;
    }

    // 4. Validate Return Date (Required)
    if (!formState.endDate) {
      setFormError("Return date is required. Please choose a return date from the calendar.");
      return;
    }

    if (formState.endDate < formState.startDate) {
      setFormError("Return date cannot be earlier than departure date.");
      return;
    }

    // 5. Validate Travellers (Required)
    if ((formState.adults || 0) < 1) {
      setFormError("At least 1 adult traveller is required.");
      return;
    }

    // 6. Validate Cabin Class (Required)
    if (!formState.cabinClass) {
      setFormError("Cabin class is required. Please choose Economy, Premium Economy, Business, or First.");
      return;
    }

    // 7. Validate Flight Stops (Required)
    if (!formState.maxStops) {
      setFormError("Flight stop preference is required.");
      return;
    }

    // 8. Validate Total Budget (Required)
    if (!formState.budget || formState.budget <= 0) {
      setFormError("Total budget is required and must be greater than INR 0.");
      return;
    }

    if (isLoading) return;
    setIsTravellersOpen(false);
    setIsCabinOpen(false);
    setIsStopsOpen(false);
    planTrip();
  };

  const totalTravellers =
    (formState.adults || 1) + (formState.children || 0) + (formState.infants || 0);

  const passengerSummary = [
    `${formState.adults || 1} Adult${(formState.adults || 1) > 1 ? "s" : ""}`,
    (formState.children || 0) > 0
      ? `${formState.children} Child${(formState.children || 0) > 1 ? "ren" : ""}`
      : null,
    (formState.infants || 0) > 0
      ? `${formState.infants} Infant${(formState.infants || 0) > 1 ? "s" : ""}`
      : null,
  ]
    .filter(Boolean)
    .join(", ");

  const currentCabin =
    CABIN_OPTIONS.find((c) => c.id === (formState.cabinClass || "ECONOMY")) || CABIN_OPTIONS[0];

  const currentStops =
    STOPS_OPTIONS.find((s) => s.id === (formState.maxStops || "ANY")) || STOPS_OPTIONS[0];

  return (
    <section className="relative bg-[#FAF9F6] pt-10 pb-36 sm:pt-14 sm:pb-48 border-b border-stone-200/60">
      {/* Subtle Scenic Backdrop */}
      <div className="absolute inset-0 z-0 opacity-15 pointer-events-none overflow-hidden">
        <div
          className="w-full h-full bg-cover bg-center"
          style={{
            backgroundImage:
              'url("https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1920&q=80")',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-[#FAF9F6]/80 via-[#FAF9F6]/95 to-[#FAF9F6]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Top Tag */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-50 border border-emerald-200/70 text-emerald-900 text-xs font-medium mb-6 shadow-2xs">
          <Sparkles className="h-3.5 w-3.5 text-[#1B4332]" />
          <span>AI Travel Agent • Dual-Leg Live Flight & Accommodation Intelligence</span>
        </div>

        {/* Heading */}
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight text-stone-900 max-w-3xl mx-auto leading-tight">
          Plan Your Next Journey with AI
        </h1>

        {/* Supporting description */}
        <p className="mt-4 text-sm sm:text-base md:text-lg text-stone-600 max-w-2xl mx-auto font-normal leading-relaxed">
          Choose your travel dates, passengers, cabin class, and stops to find the best flights with complete booking links.
        </p>

        {/* Quick Popular Places */}
        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          <span className="text-xs font-semibold text-stone-600 mr-1 flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-[#1B4332]" />
            <span>Popular Places for Trip:</span>
          </span>
          {POPULAR_PLACES.map((place) => {
            const isSelected = formState.destination.toLowerCase().includes(place.name.toLowerCase().split(",")[0].trim());
            return (
              <button
                key={place.name}
                type="button"
                onClick={() => handleSelectPlace(place)}
                className={`text-xs font-medium px-3.5 py-1.5 rounded-full border transition-all shadow-2xs cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? "bg-emerald-50 border-emerald-600 text-emerald-900 font-bold ring-1 ring-emerald-600/30"
                    : "bg-white border-stone-200/90 text-stone-700 hover:border-emerald-600 hover:text-emerald-800"
                }`}
              >
                <span>{place.emoji}</span>
                <span>{place.name.split(",")[0]}</span>
              </button>
            );
          })}
        </div>

        {/* Trip Planning Form Card */}
        <div className="mt-8 bg-white rounded-2xl shadow-md border border-stone-200/90 p-5 sm:p-7 text-left max-w-4xl mx-auto">
          {/* Validation Alert */}
          {formError && (
            <div className="mb-4 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-700 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Row 1: Origin, Destination, Going Date, Return Date */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Origin City */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Plane className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Origin City / Airport <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                </label>
                <input
                  type="text"
                  required
                  value={formState.origin}
                  onChange={(e) => updateFormState({ origin: e.target.value })}
                  placeholder="Kolkata (CCU)"
                  className="w-full h-11 px-3 text-sm text-stone-900 bg-stone-50/60 border border-stone-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] transition-all font-medium"
                />
              </div>

              {/* Destination */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Destination <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                </label>
                <input
                  type="text"
                  required
                  value={formState.destination}
                  onChange={(e) => updateFormState({ destination: e.target.value })}
                  placeholder="Bengaluru (BLR)"
                  className="w-full h-11 px-3 text-sm text-stone-900 bg-stone-50/60 border border-stone-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] transition-all font-medium"
                />
              </div>

              {/* Calendar Picker: Departure Date (Mandatory) */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Going Date <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                </label>
                <input
                  type="date"
                  required
                  min={todayStr}
                  value={formState.startDate}
                  onChange={(e) => handleStartDateChange(e.target.value)}
                  className="w-full h-11 px-3 text-sm text-stone-900 bg-stone-50/60 border border-stone-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] transition-all cursor-pointer font-medium"
                />
              </div>

              {/* Calendar Picker: Return Date (Mandatory) */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Return Date <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                </label>
                <input
                  type="date"
                  required
                  min={formState.startDate || todayStr}
                  value={formState.endDate}
                  onChange={(e) => handleEndDateChange(e.target.value)}
                  className="w-full h-11 px-3 text-sm text-stone-900 bg-stone-50/60 border border-stone-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] transition-all cursor-pointer font-medium"
                />
              </div>
            </div>

            {/* Row 2: Travellers, Cabin Class, Flight Stops, Total Budget */}
            <div className="pt-2 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
              {/* Box 1: Travellers Selector */}
              <div className="space-y-1.5 relative" ref={travellersRef}>
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Users className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Travellers <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                  <span className="text-[10px] text-emerald-800 font-bold bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200/60">
                    {totalTravellers} Pax
                  </span>
                </label>

                {/* Trigger Button */}
                <button
                  type="button"
                  onClick={() => {
                    setIsTravellersOpen(!isTravellersOpen);
                    setIsCabinOpen(false);
                    setIsStopsOpen(false);
                  }}
                  className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                    isTravellersOpen
                      ? "bg-white border-2 border-[#1B4332] shadow-xs"
                      : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                  }`}
                >
                  <span className="truncate font-semibold text-xs sm:text-sm text-stone-800">
                    {passengerSummary}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 text-stone-500 shrink-0 ml-1 transition-transform duration-200 ${
                      isTravellersOpen ? "rotate-180 text-[#1B4332]" : ""
                    }`}
                  />
                </button>

                {/* Professional Travellers Dropdown */}
                {isTravellersOpen && (
                  <div className="absolute left-0 top-full mt-2 w-[290px] sm:w-[310px] max-w-[calc(100vw-2.5rem)] p-3 bg-white rounded-2xl shadow-2xl border border-stone-200/90 z-50 space-y-3 animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="flex items-center justify-between pb-2 border-b border-stone-100">
                      <span className="text-xs font-bold text-stone-900">
                        Configure Passengers
                      </span>
                      <span className="text-[11px] text-stone-500 font-medium">
                        {totalTravellers} Total
                      </span>
                    </div>

                    {/* Adults Stepper */}
                    <div className="flex items-center justify-between py-1">
                      <div>
                        <p className="text-xs font-semibold text-stone-800">Adults</p>
                        <p className="text-[11px] text-stone-500">Age 12+ years</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          disabled={(formState.adults || 1) <= 1}
                          onClick={() =>
                            handlePassengerChange("adults", Math.max(1, (formState.adults || 1) - 1))
                          }
                          className="h-8 w-8 rounded-lg border border-stone-200 bg-stone-50 flex items-center justify-center text-stone-700 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="w-5 text-center text-sm font-bold text-stone-900">
                          {formState.adults || 1}
                        </span>
                        <button
                          type="button"
                          disabled={(formState.adults || 1) >= 9}
                          onClick={() =>
                            handlePassengerChange("adults", Math.min(9, (formState.adults || 1) + 1))
                          }
                          className="h-8 w-8 rounded-lg border border-stone-200 bg-stone-50 flex items-center justify-center text-stone-700 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Children Stepper */}
                    <div className="flex items-center justify-between py-1">
                      <div>
                        <p className="text-xs font-semibold text-stone-800">Children</p>
                        <p className="text-[11px] text-stone-500">Age 2–11 years</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          disabled={(formState.children || 0) <= 0}
                          onClick={() =>
                            handlePassengerChange("children", Math.max(0, (formState.children || 0) - 1))
                          }
                          className="h-8 w-8 rounded-lg border border-stone-200 bg-stone-50 flex items-center justify-center text-stone-700 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="w-5 text-center text-sm font-bold text-stone-900">
                          {formState.children || 0}
                        </span>
                        <button
                          type="button"
                          disabled={(formState.children || 0) >= 9}
                          onClick={() =>
                            handlePassengerChange("children", Math.min(9, (formState.children || 0) + 1))
                          }
                          className="h-8 w-8 rounded-lg border border-stone-200 bg-stone-50 flex items-center justify-center text-stone-700 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Infants Stepper */}
                    <div className="flex items-center justify-between py-1">
                      <div>
                        <p className="text-xs font-semibold text-stone-800">Infants</p>
                        <p className="text-[11px] text-stone-500">Under 2 years</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          disabled={(formState.infants || 0) <= 0}
                          onClick={() =>
                            handlePassengerChange("infants", Math.max(0, (formState.infants || 0) - 1))
                          }
                          className="h-8 w-8 rounded-lg border border-stone-200 bg-stone-50 flex items-center justify-center text-stone-700 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                        >
                          <Minus className="h-3.5 w-3.5" />
                        </button>
                        <span className="w-5 text-center text-sm font-bold text-stone-900">
                          {formState.infants || 0}
                        </span>
                        <button
                          type="button"
                          disabled={(formState.infants || 0) >= 4}
                          onClick={() =>
                            handlePassengerChange("infants", Math.min(4, (formState.infants || 0) + 1))
                          }
                          className="h-8 w-8 rounded-lg border border-stone-200 bg-stone-50 flex items-center justify-center text-stone-700 hover:bg-stone-100 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer transition-colors"
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Done Action */}
                    <div className="pt-2 border-t border-stone-100 flex items-center justify-between">
                      <span className="text-[11px] text-stone-500 font-medium">
                        {totalTravellers} Total
                      </span>
                      <button
                        type="button"
                        onClick={() => setIsTravellersOpen(false)}
                        className="px-4 py-1.5 bg-[#1B4332] text-white text-xs font-bold rounded-lg hover:bg-[#2D6A4F] transition-all cursor-pointer shadow-xs"
                      >
                        Done
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Box 2: Cabin Class (Custom Structured Selector) */}
              <div className="space-y-1.5 relative" ref={cabinRef}>
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Armchair className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Cabin Class <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                  <span className="text-[10px] text-stone-500 font-medium">
                    {currentCabin.badge}
                  </span>
                </label>

                <button
                  type="button"
                  onClick={() => {
                    setIsCabinOpen(!isCabinOpen);
                    setIsStopsOpen(false);
                    setIsTravellersOpen(false);
                  }}
                  className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                    isCabinOpen
                      ? "bg-white border-2 border-[#1B4332] shadow-xs"
                      : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                  }`}
                >
                  <span className="truncate font-semibold text-xs sm:text-sm text-stone-800">
                    {currentCabin.label}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 text-stone-500 shrink-0 ml-1 transition-transform duration-200 ${
                      isCabinOpen ? "rotate-180 text-[#1B4332]" : ""
                    }`}
                  />
                </button>

                {/* Professional Rounded Options Popover (Positioned safely below field) */}
                {isCabinOpen && (
                  <div className="absolute left-0 top-full mt-2 w-full sm:w-[310px] z-50 p-2 bg-white rounded-2xl shadow-2xl border border-stone-200/90 space-y-1.5 animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="px-2.5 pt-1 pb-1 text-[11px] font-bold text-stone-400 uppercase tracking-wider">
                      Select Travel Class
                    </div>
                    {CABIN_OPTIONS.map((opt) => {
                      const isSelected = (formState.cabinClass || "ECONOMY") === opt.id;
                      return (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => {
                            updateFormState({ cabinClass: opt.id });
                            setIsCabinOpen(false);
                          }}
                          className={`w-full p-2.5 rounded-xl text-left transition-all flex items-center justify-between cursor-pointer ${
                            isSelected
                              ? "bg-emerald-50/90 border border-emerald-300/80 shadow-2xs text-[#1B4332]"
                              : "hover:bg-stone-100/70 border border-transparent text-stone-800"
                          }`}
                        >
                          <div className="pr-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs sm:text-sm font-bold">
                                {opt.label}
                              </span>
                              <span
                                className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                                  isSelected
                                    ? "bg-emerald-200/80 text-emerald-900"
                                    : "bg-stone-100 text-stone-500"
                                }`}
                              >
                                {opt.badge}
                              </span>
                            </div>
                            <p className="text-[11px] text-stone-500 mt-0.5 font-normal leading-snug">
                              {opt.description}
                            </p>
                          </div>
                          {isSelected && (
                            <div className="h-5 w-5 rounded-full bg-[#1B4332] text-white flex items-center justify-center shrink-0">
                              <Check className="h-3 w-3 stroke-[3]" />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Box 3: Flight Stops (Custom Structured Selector) */}
              <div className="space-y-1.5 relative" ref={stopsRef}>
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <SlidersHorizontal className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Flight Stops <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                  <span className="text-[10px] text-stone-500 font-medium">
                    {currentStops.badge}
                  </span>
                </label>

                <button
                  type="button"
                  onClick={() => {
                    setIsStopsOpen(!isStopsOpen);
                    setIsCabinOpen(false);
                    setIsTravellersOpen(false);
                  }}
                  className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                    isStopsOpen
                      ? "bg-white border-2 border-[#1B4332] shadow-xs"
                      : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                  }`}
                >
                  <span className="truncate font-semibold text-xs sm:text-sm text-stone-800">
                    {currentStops.label}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 text-stone-500 shrink-0 ml-1 transition-transform duration-200 ${
                      isStopsOpen ? "rotate-180 text-[#1B4332]" : ""
                    }`}
                  />
                </button>

                {/* Professional Rounded Options Popover (Positioned safely below field) */}
                {isStopsOpen && (
                  <div className="absolute left-0 sm:left-auto sm:right-0 top-full mt-2 w-full sm:w-[310px] z-50 p-2 bg-white rounded-2xl shadow-2xl border border-stone-200/90 space-y-1.5 animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="px-2.5 pt-1 pb-1 text-[11px] font-bold text-stone-400 uppercase tracking-wider">
                      Routing & Layovers
                    </div>
                    {STOPS_OPTIONS.map((opt) => {
                      const isSelected = (formState.maxStops || "ANY") === opt.id;
                      return (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => {
                            updateFormState({ maxStops: opt.id });
                            setIsStopsOpen(false);
                          }}
                          className={`w-full p-2.5 rounded-xl text-left transition-all flex items-center justify-between cursor-pointer ${
                            isSelected
                              ? "bg-emerald-50/90 border border-emerald-300/80 shadow-2xs text-[#1B4332]"
                              : "hover:bg-stone-100/70 border border-transparent text-stone-800"
                          }`}
                        >
                          <div className="pr-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs sm:text-sm font-bold">
                                {opt.label}
                              </span>
                              <span
                                className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                                  isSelected
                                    ? "bg-emerald-200/80 text-emerald-900"
                                    : "bg-stone-100 text-stone-500"
                                }`}
                              >
                                {opt.badge}
                              </span>
                            </div>
                            <p className="text-[11px] text-stone-500 mt-0.5 font-normal leading-snug">
                              {opt.description}
                            </p>
                          </div>
                          {isSelected && (
                            <div className="h-5 w-5 rounded-full bg-[#1B4332] text-white flex items-center justify-center shrink-0">
                              <Check className="h-3 w-3 stroke-[3]" />
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Box 4: Total Budget */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <IndianRupee className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Total Budget (INR) <span className="text-rose-500 font-bold">*</span></span>
                  </span>
                </label>
                <input
                  type="number"
                  step="1000"
                  min="5000"
                  max="10000000"
                  required
                  value={formState.budget || ""}
                  onChange={(e) =>
                    updateFormState({ budget: parseFloat(e.target.value) || 0 })
                  }
                  placeholder="90000"
                  className="w-full h-11 px-3 text-sm text-stone-900 bg-stone-50/60 border border-stone-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332] transition-all font-medium"
                />
              </div>
            </div>

            {/* Row 3: Prominent Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full h-12 px-6 bg-[#1B4332] hover:bg-[#2D6A4F] text-white text-base font-semibold rounded-xl flex items-center justify-center gap-2 shadow-sm transition-all duration-150 disabled:opacity-75 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin text-emerald-200" />
                    <span>Plan Trip</span>
                  </>
                ) : (
                  <span>Plan Trip</span>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  );
}
