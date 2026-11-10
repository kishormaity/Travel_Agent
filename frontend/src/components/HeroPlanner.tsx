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
  Search,
  ChevronLeft,
  ChevronRight,
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

export const ORIGIN_OPTIONS = [
  { city: "Delhi", iata: "DEL", label: "Delhi (DEL)", subtext: "Indira Gandhi Int'l Airport", emoji: "🏛️" },
  { city: "Mumbai", iata: "BOM", label: "Mumbai (BOM)", subtext: "Chhatrapati Shivaji Maharaj Int'l", emoji: "🌊" },
  { city: "Bengaluru", iata: "BLR", label: "Bengaluru (BLR)", subtext: "Kempegowda Int'l Airport", emoji: "🏙️" },
  { city: "Kolkata", iata: "CCU", label: "Kolkata (CCU)", subtext: "Netaji Subhash Chandra Bose Int'l", emoji: "🚋" },
  { city: "Chennai", iata: "MAA", label: "Chennai (MAA)", subtext: "Chennai Int'l Airport", emoji: "🛕" },
  { city: "Hyderabad", iata: "HYD", label: "Hyderabad (HYD)", subtext: "Rajiv Gandhi Int'l Airport", emoji: "💎" },
  { city: "Ahmedabad", iata: "AMD", label: "Ahmedabad (AMD)", subtext: "Sardar Vallabhbhai Patel Int'l", emoji: "🪁" },
  { city: "Pune", iata: "PNQ", label: "Pune (PNQ)", subtext: "Pune International Airport", emoji: "⛰️" },
  { city: "Jaipur", iata: "JAI", label: "Jaipur (JAI)", subtext: "Jaipur Int'l Airport", emoji: "🏰" },
  { city: "Kochi", iata: "COK", label: "Kochi (COK)", subtext: "Cochin Int'l Airport", emoji: "🌴" },
  { city: "Goa", iata: "GOI", label: "Goa (GOI)", subtext: "Dabolim / Mopa (GOX)", emoji: "🏖️" },
  { city: "Lucknow", iata: "LKO", label: "Lucknow (LKO)", subtext: "Chaudhary Charan Singh Int'l", emoji: "🕌" },
  { city: "Chandigarh", iata: "IXC", label: "Chandigarh (IXC)", subtext: "Shaheed Bhagat Singh Int'l", emoji: "🌹" },
  { city: "Varanasi", iata: "VNS", label: "Varanasi (VNS)", subtext: "Lal Bahadur Shastri Int'l", emoji: "🪔" },
  { city: "Amritsar", iata: "ATQ", label: "Amritsar (ATQ)", subtext: "Sri Guru Ram Dass Jee Int'l", emoji: "✨" },
  { city: "Udaipur", iata: "UDR", label: "Udaipur (UDR)", subtext: "Maharana Pratap Airport", emoji: "👑" },
] as const;

export const DESTINATION_OPTIONS = [
  { city: "Bengaluru", iata: "BLR", label: "Bengaluru (BLR)", subtext: "Gardens, Lalbagh & Tech Capital", emoji: "🏙️", suggestedBudget: 60000 },
  { city: "Jaipur", iata: "JAI", label: "Jaipur (JAI)", subtext: "Amer Fort, Hawa Mahal & Palaces", emoji: "🏰", suggestedBudget: 55000 },
  { city: "Goa", iata: "GOI", label: "Goa (GOI)", subtext: "Calangute, Palolem & Beaches", emoji: "🏖️", suggestedBudget: 45000 },
  { city: "Kochi & Munnar", iata: "COK", label: "Kochi & Munnar, Kerala", subtext: "Backwaters, Tea Hills & Houseboats", emoji: "🌴", suggestedBudget: 65000 },
  { city: "Udaipur", iata: "UDR", label: "Udaipur (UDR)", subtext: "City of Lakes & Royal City Palace", emoji: "👑", suggestedBudget: 60000 },
  { city: "Delhi", iata: "DEL", label: "Delhi (DEL)", subtext: "India Gate, Red Fort & Qutb Minar", emoji: "🏛️", suggestedBudget: 50000 },
  { city: "Mumbai", iata: "BOM", label: "Mumbai (BOM)", subtext: "Marine Drive & Gateway of India", emoji: "🌊", suggestedBudget: 65000 },
  { city: "Varanasi", iata: "VNS", label: "Varanasi (VNS)", subtext: "Spiritual Ghats & Ganga Aarti", emoji: "🪔", suggestedBudget: 35000 },
  { city: "Srinagar & Gulmarg", iata: "SXR", label: "Srinagar & Gulmarg, Kashmir", subtext: "Dal Lake, Shikaras & Snow Valleys", emoji: "🌸", suggestedBudget: 75000 },
  { city: "Manali & Shimla", iata: "IXC", label: "Manali & Shimla, Himachal", subtext: "Snow Valleys & Himalayan Passes", emoji: "🏔️", suggestedBudget: 50000 },
  { city: "Kolkata", iata: "CCU", label: "Kolkata (CCU)", subtext: "Victoria Memorial & Howrah Bridge", emoji: "🚋", suggestedBudget: 45000 },
  { city: "Hyderabad", iata: "HYD", label: "Hyderabad (HYD)", subtext: "Charminar, Golconda & Pearls", emoji: "💎", suggestedBudget: 50000 },
  { city: "Amritsar", iata: "ATQ", label: "Amritsar (ATQ)", subtext: "Golden Temple & Wagah Border", emoji: "✨", suggestedBudget: 40000 },
  { city: "Jodhpur", iata: "JDH", label: "Jodhpur (JDH)", subtext: "Mehrangarh Fort & Blue City", emoji: "💙", suggestedBudget: 50000 },
  { city: "Agra", iata: "AGR", label: "Agra (AGR)", subtext: "Taj Mahal & Mughal Architecture", emoji: "🕌", suggestedBudget: 40000 },
  { city: "Chennai", iata: "MAA", label: "Chennai (MAA)", subtext: "Marina Beach & Shore Temples", emoji: "🛕", suggestedBudget: 50000 },
] as const;

export function HeroPlanner() {
  const { formState, updateFormState, planTrip, isLoading } = useTripStore();
  const [formError, setFormError] = useState<string | null>(null);
  const [todayStr, setTodayStr] = useState("");

  const [isOriginOpen, setIsOriginOpen] = useState(false);
  const [isDestinationOpen, setIsDestinationOpen] = useState(false);
  const [originSearch, setOriginSearch] = useState("");
  const [destinationSearch, setDestinationSearch] = useState("");
  const [isTravellersOpen, setIsTravellersOpen] = useState(false);
  const [isCabinOpen, setIsCabinOpen] = useState(false);
  const [isStopsOpen, setIsStopsOpen] = useState(false);

  // Professional Interactive Calendar System State
  const [isDatePickerOpen, setIsDatePickerOpen] = useState(false);
  const [activeDateField, setActiveDateField] = useState<"going" | "return">("going");
  const [viewYear, setViewYear] = useState(2026);
  const [viewMonth, setViewMonth] = useState(10); // 0-indexed: 10 = November

  const originRef = useRef<HTMLDivElement>(null);
  const destinationRef = useRef<HTMLDivElement>(null);
  const travellersRef = useRef<HTMLDivElement>(null);
  const cabinRef = useRef<HTMLDivElement>(null);
  const stopsRef = useRef<HTMLDivElement>(null);
  const datePickerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTodayStr(new Date().toISOString().split("T")[0]);

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (originRef.current && !originRef.current.contains(target)) {
        setIsOriginOpen(false);
        setOriginSearch("");
      }
      if (destinationRef.current && !destinationRef.current.contains(target)) {
        setIsDestinationOpen(false);
        setDestinationSearch("");
      }
      if (datePickerRef.current && !datePickerRef.current.contains(target)) {
        setIsDatePickerOpen(false);
      }
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

  const selectedOrigin = ORIGIN_OPTIONS.find(
    (o) =>
      formState.origin.toLowerCase().includes(o.iata.toLowerCase()) ||
      formState.origin.toLowerCase().includes(o.city.toLowerCase())
  );

  const selectedDestination = DESTINATION_OPTIONS.find(
    (d) =>
      formState.destination.toLowerCase().includes(d.iata.toLowerCase()) ||
      formState.destination.toLowerCase().includes(d.city.toLowerCase().split(" ")[0])
  );

  const filteredOrigins = ORIGIN_OPTIONS.filter((o) => {
    if (!originSearch.trim()) return true;
    const q = originSearch.toLowerCase().trim();
    return (
      o.city.toLowerCase().includes(q) ||
      o.iata.toLowerCase().includes(q) ||
      o.label.toLowerCase().includes(q) ||
      o.subtext.toLowerCase().includes(q)
    );
  });

  const filteredDestinations = DESTINATION_OPTIONS.filter((d) => {
    if (!destinationSearch.trim()) return true;
    const q = destinationSearch.toLowerCase().trim();
    return (
      d.city.toLowerCase().includes(q) ||
      d.iata.toLowerCase().includes(q) ||
      d.label.toLowerCase().includes(q) ||
      d.subtext.toLowerCase().includes(q)
    );
  });

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

  const openDatePicker = (field: "going" | "return") => {
    setActiveDateField(field);
    setIsDatePickerOpen(true);
    setIsOriginOpen(false);
    setIsDestinationOpen(false);
    setIsCabinOpen(false);
    setIsStopsOpen(false);
    setIsTravellersOpen(false);

    const targetDate = field === "return" && formState.endDate ? formState.endDate : formState.startDate;
    if (targetDate) {
      const parts = targetDate.split("-").map(Number);
      if (parts[0] && parts[1]) {
        setViewYear(parts[0]);
        setViewMonth(parts[1] - 1);
      }
    }
  };

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const handlePrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((y) => y - 1);
    } else {
      setViewMonth((m) => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((y) => y + 1);
    } else {
      setViewMonth((m) => m + 1);
    }
  };

  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDayIndex = new Date(viewYear, viewMonth, 1).getDay(); // 0 is Sunday

  const isPastDate = (day: number) => {
    if (!todayStr) return false;
    const formattedMonth = String(viewMonth + 1).padStart(2, "0");
    const formattedDay = String(day).padStart(2, "0");
    const cellDateStr = `${viewYear}-${formattedMonth}-${formattedDay}`;
    return cellDateStr < todayStr;
  };

  const isSelectedStart = (day: number) => {
    if (!formState.startDate) return false;
    const formattedMonth = String(viewMonth + 1).padStart(2, "0");
    const formattedDay = String(day).padStart(2, "0");
    return `${viewYear}-${formattedMonth}-${formattedDay}` === formState.startDate;
  };

  const isSelectedEnd = (day: number) => {
    if (!formState.endDate) return false;
    const formattedMonth = String(viewMonth + 1).padStart(2, "0");
    const formattedDay = String(day).padStart(2, "0");
    return `${viewYear}-${formattedMonth}-${formattedDay}` === formState.endDate;
  };

  const isInRange = (day: number) => {
    if (!formState.startDate || !formState.endDate) return false;
    const formattedMonth = String(viewMonth + 1).padStart(2, "0");
    const formattedDay = String(day).padStart(2, "0");
    const cellDateStr = `${viewYear}-${formattedMonth}-${formattedDay}`;
    return cellDateStr > formState.startDate && cellDateStr < formState.endDate;
  };

  const handleDateClick = (day: number) => {
    const formattedMonth = String(viewMonth + 1).padStart(2, "0");
    const formattedDay = String(day).padStart(2, "0");
    const cellDateStr = `${viewYear}-${formattedMonth}-${formattedDay}`;

    if (activeDateField === "going") {
      handleStartDateChange(cellDateStr);
      setActiveDateField("return");
    } else {
      if (formState.startDate && cellDateStr < formState.startDate) {
        handleStartDateChange(cellDateStr);
        setActiveDateField("return");
      } else {
        handleEndDateChange(cellDateStr);
        setIsDatePickerOpen(false);
      }
    }
  };

  const handlePresetDays = (numDays: number) => {
    if (!formState.startDate) return;
    const [y, m, d] = formState.startDate.split("-").map(Number);
    const startObj = new Date(y, m - 1, d);
    const endObj = new Date(startObj);
    endObj.setDate(startObj.getDate() + (numDays - 1));

    const endY = endObj.getFullYear();
    const endM = String(endObj.getMonth() + 1).padStart(2, "0");
    const endD = String(endObj.getDate()).padStart(2, "0");
    const newEndStr = `${endY}-${endM}-${endD}`;

    handleEndDateChange(newEndStr);
  };

  const formatDisplayDate = (dateStr: string) => {
    if (!dateStr) return "";
    try {
      const [y, m, d] = dateStr.split("-").map(Number);
      if (!y || !m || !d) return dateStr;
      const date = new Date(y, m - 1, d);
      return date.toLocaleDateString("en-IN", {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  const formatShortDate = (dateStr: string) => {
    if (!dateStr) return "";
    try {
      const [y, m, d] = dateStr.split("-").map(Number);
      if (!y || !m || !d) return dateStr;
      const date = new Date(y, m - 1, d);
      return date.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
      });
    } catch {
      return dateStr;
    }
  };

  const getDayOfWeek = (dateStr: string) => {
    if (!dateStr) return "";
    try {
      const [y, m, d] = dateStr.split("-").map(Number);
      const date = new Date(y, m - 1, d);
      return date.toLocaleDateString("en-IN", { weekday: "long" });
    } catch {
      return "";
    }
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
              {/* Origin City / Airport */}
              <div className="space-y-1.5 relative" ref={originRef}>
                <label className="text-xs font-semibold text-stone-700 flex items-center gap-1.5">
                  <Plane className="h-3.5 w-3.5 text-[#1B4332]" />
                  <span>Origin City / Airport <span className="text-rose-500 font-bold">*</span></span>
                </label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => {
                      setIsOriginOpen(!isOriginOpen);
                      setIsDestinationOpen(false);
                      setIsCabinOpen(false);
                      setIsStopsOpen(false);
                      setIsTravellersOpen(false);
                      setOriginSearch("");
                    }}
                    className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                      isOriginOpen
                        ? "bg-white border-2 border-[#1B4332] shadow-xs"
                        : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-base">{selectedOrigin?.emoji || "🛫"}</span>
                      <span className="font-semibold text-xs sm:text-sm text-stone-800 truncate">
                        {formState.origin || "Select Departure City"}
                      </span>
                    </div>
                    <ChevronDown
                      className={`h-4 w-4 text-stone-500 shrink-0 ml-1 transition-transform duration-200 ${
                        isOriginOpen ? "rotate-180 text-[#1B4332]" : ""
                      }`}
                    />
                  </button>
                </div>

                {/* Popover Options List (All 16 Available) */}
                {isOriginOpen && (
                  <div className="absolute left-0 top-full mt-2 w-full sm:w-[320px] max-h-80 overflow-hidden z-50 bg-white rounded-2xl shadow-2xl border border-stone-200/90 flex flex-col animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="p-2 border-b border-stone-100">
                      <div className="relative">
                        <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-stone-400" />
                        <input
                          type="text"
                          value={originSearch}
                          onChange={(e) => setOriginSearch(e.target.value)}
                          placeholder="Search 16 origin cities..."
                          className="w-full h-8 pl-8 pr-3 text-xs bg-stone-50 border border-stone-200 rounded-lg focus:outline-none focus:bg-white focus:border-[#1B4332]"
                          autoFocus
                        />
                      </div>
                    </div>

                    <div className="p-1.5 overflow-y-auto max-h-64 space-y-1">
                      <div className="px-2.5 pt-1 pb-1 text-[11px] font-bold text-stone-400 uppercase tracking-wider flex items-center justify-between">
                        <span>Select Departure City</span>
                        <span className="text-[10px] text-emerald-700 font-semibold">{filteredOrigins.length} Cities</span>
                      </div>
                      {filteredOrigins.map((opt) => {
                        const isSelected = formState.origin.toLowerCase().includes(opt.iata.toLowerCase());
                        return (
                          <button
                            key={opt.iata}
                            type="button"
                            onClick={() => {
                              updateFormState({ origin: opt.label });
                              setOriginSearch("");
                              setIsOriginOpen(false);
                            }}
                            className={`w-full p-2.5 rounded-xl text-left transition-all flex items-center justify-between cursor-pointer ${
                              isSelected
                                ? "bg-emerald-50/90 border border-emerald-300/80 shadow-2xs text-[#1B4332]"
                                : "hover:bg-stone-100/70 border border-transparent text-stone-800"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 pr-2">
                              <span className="text-base">{opt.emoji}</span>
                              <div>
                                <div className="flex items-center gap-1.5">
                                  <span className="text-xs sm:text-sm font-bold text-stone-900">{opt.city}</span>
                                  <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800">{opt.iata}</span>
                                </div>
                                <p className="text-[11px] text-stone-500 font-normal leading-tight">{opt.subtext}</p>
                              </div>
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
                  </div>
                )}
              </div>

              {/* Destination */}
              <div className="space-y-1.5 relative" ref={destinationRef}>
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-stone-700 flex items-center gap-1.5">
                    <MapPin className="h-3.5 w-3.5 text-[#1B4332]" />
                    <span>Destination <span className="text-rose-500 font-bold">*</span></span>
                  </label>
                </div>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => {
                      setIsDestinationOpen(!isDestinationOpen);
                      setIsOriginOpen(false);
                      setIsCabinOpen(false);
                      setIsStopsOpen(false);
                      setIsTravellersOpen(false);
                      setDestinationSearch("");
                    }}
                    className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                      isDestinationOpen
                        ? "bg-white border-2 border-[#1B4332] shadow-xs"
                        : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-base">{selectedDestination?.emoji || "📍"}</span>
                      <span className="font-semibold text-xs sm:text-sm text-stone-800 truncate">
                        {formState.destination || "Select Destination"}
                      </span>
                    </div>
                    <ChevronDown
                      className={`h-4 w-4 text-stone-500 shrink-0 ml-1 transition-transform duration-200 ${
                        isDestinationOpen ? "rotate-180 text-[#1B4332]" : ""
                      }`}
                    />
                  </button>
                </div>

                {/* Popover Options List (All 16 Available) */}
                {isDestinationOpen && (
                  <div className="absolute left-0 top-full mt-2 w-full sm:w-[320px] max-h-80 overflow-hidden z-50 bg-white rounded-2xl shadow-2xl border border-stone-200/90 flex flex-col animate-in fade-in slide-in-from-top-1 duration-150">
                    <div className="p-2 border-b border-stone-100">
                      <div className="relative">
                        <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-stone-400" />
                        <input
                          type="text"
                          value={destinationSearch}
                          onChange={(e) => setDestinationSearch(e.target.value)}
                          placeholder="Search 16 destinations..."
                          className="w-full h-8 pl-8 pr-3 text-xs bg-stone-50 border border-stone-200 rounded-lg focus:outline-none focus:bg-white focus:border-[#1B4332]"
                          autoFocus
                        />
                      </div>
                    </div>

                    <div className="p-1.5 overflow-y-auto max-h-64 space-y-1">
                      <div className="px-2.5 pt-1 pb-1 text-[11px] font-bold text-stone-400 uppercase tracking-wider flex items-center justify-between">
                        <span>Select Destination</span>
                        <span className="text-[10px] text-emerald-700 font-semibold">{filteredDestinations.length} Places</span>
                      </div>
                      {filteredDestinations.map((place) => {
                        const isSelected = formState.destination.toLowerCase().includes(place.city.toLowerCase().split(" ")[0]);
                        return (
                          <button
                            key={place.iata + place.city}
                            type="button"
                            onClick={() => {
                              updateFormState({
                                destination: place.label,
                                budget: formState.budget || place.suggestedBudget,
                              });
                              setDestinationSearch("");
                              setIsDestinationOpen(false);
                            }}
                            className={`w-full p-2.5 rounded-xl text-left transition-all flex items-center justify-between cursor-pointer ${
                              isSelected
                                ? "bg-emerald-50/90 border border-emerald-300/80 shadow-2xs text-[#1B4332]"
                                : "hover:bg-stone-100/70 border border-transparent text-stone-800"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 pr-2">
                              <span className="text-base">{place.emoji}</span>
                              <div>
                                <div className="flex items-center gap-1.5">
                                  <span className="text-xs sm:text-sm font-bold text-stone-900">{place.city}</span>
                                  <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800">{place.iata}</span>
                                </div>
                                <p className="text-[11px] text-stone-500 font-normal leading-tight">{place.subtext}</p>
                              </div>
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
                  </div>
                )}
              </div>

              {/* Professional Flight Calendar System */}
              <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4 relative" ref={datePickerRef}>
                {/* Going Date Card */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-[#1B4332]" />
                      <span>Going Date <span className="text-rose-500 font-bold">*</span></span>
                    </span>
                    {formState.startDate && (
                      <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200/60">
                        {getDayOfWeek(formState.startDate)}
                      </span>
                    )}
                  </label>
                  <button
                    type="button"
                    onClick={() => openDatePicker("going")}
                    className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                      isDatePickerOpen && activeDateField === "going"
                        ? "bg-white border-2 border-[#1B4332] shadow-xs"
                        : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-[10px] font-bold text-[#1B4332] bg-emerald-100/70 px-1.5 py-0.5 rounded">DEP</span>
                      <span className="font-semibold text-xs sm:text-sm text-stone-800 truncate">
                        {formatDisplayDate(formState.startDate) || "Select Departure"}
                      </span>
                    </div>
                    <Calendar className="h-4 w-4 text-stone-400 group-hover:text-[#1B4332]" />
                  </button>
                  <input
                    type="date"
                    required
                    value={formState.startDate}
                    onChange={(e) => handleStartDateChange(e.target.value)}
                    className="sr-only"
                    tabIndex={-1}
                  />
                </div>

                {/* Return Date Card */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-stone-700 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="h-3.5 w-3.5 text-[#1B4332]" />
                      <span>Return Date <span className="text-rose-500 font-bold">*</span></span>
                    </span>
                    {formState.days > 0 && (
                      <span className="text-[10px] font-bold text-emerald-800 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200/60">
                        {formState.days} Days Trip
                      </span>
                    )}
                  </label>
                  <button
                    type="button"
                    onClick={() => openDatePicker("return")}
                    className={`w-full h-11 px-3 text-sm text-left text-stone-900 rounded-xl transition-all flex items-center justify-between cursor-pointer ${
                      isDatePickerOpen && activeDateField === "return"
                        ? "bg-white border-2 border-[#1B4332] shadow-xs"
                        : "bg-stone-50/60 border border-stone-200 hover:bg-white focus:bg-white focus:ring-2 focus:ring-[#1B4332]/20 focus:border-[#1B4332]"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span className="text-[10px] font-bold text-emerald-800 bg-emerald-100/70 px-1.5 py-0.5 rounded">RET</span>
                      <span className="font-semibold text-xs sm:text-sm text-stone-800 truncate">
                        {formatDisplayDate(formState.endDate) || "Select Return"}
                      </span>
                    </div>
                    <Calendar className="h-4 w-4 text-stone-400 group-hover:text-[#1B4332]" />
                  </button>
                  <input
                    type="date"
                    required
                    value={formState.endDate}
                    onChange={(e) => handleEndDateChange(e.target.value)}
                    className="sr-only"
                    tabIndex={-1}
                  />
                </div>

                {/* Professional Interactive Calendar Popover */}
                {isDatePickerOpen && (
                  <div className="absolute right-0 top-full mt-2 w-full sm:w-[380px] p-4 bg-white rounded-2xl shadow-2xl border border-stone-200/90 z-50 animate-in fade-in slide-in-from-top-1 duration-150">
                    {/* Header: Mode Selector */}
                    <div className="flex items-center gap-1.5 p-1 bg-stone-100 rounded-xl mb-3">
                      <button
                        type="button"
                        onClick={() => setActiveDateField("going")}
                        className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                          activeDateField === "going"
                            ? "bg-white text-[#1B4332] shadow-xs border border-stone-200/80 font-bold"
                            : "text-stone-600 hover:text-stone-900"
                        }`}
                      >
                        <span>🛫 Going:</span>
                        <span className="truncate">{formState.startDate ? formatShortDate(formState.startDate) : "Pick Date"}</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => setActiveDateField("return")}
                        className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                          activeDateField === "return"
                            ? "bg-white text-[#1B4332] shadow-xs border border-stone-200/80 font-bold"
                            : "text-stone-600 hover:text-stone-900"
                        }`}
                      >
                        <span>🛬 Return:</span>
                        <span className="truncate">{formState.endDate ? formatShortDate(formState.endDate) : "Pick Date"}</span>
                      </button>
                    </div>

                    {/* Month Navigator */}
                    <div className="flex items-center justify-between mb-3 px-1">
                      <button
                        type="button"
                        onClick={handlePrevMonth}
                        className="p-1.5 rounded-lg text-stone-600 hover:text-stone-900 hover:bg-stone-100 transition-colors cursor-pointer"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </button>
                      <span className="text-xs sm:text-sm font-bold text-stone-900">
                        {monthNames[viewMonth]} {viewYear}
                      </span>
                      <button
                        type="button"
                        onClick={handleNextMonth}
                        className="p-1.5 rounded-lg text-stone-600 hover:text-stone-900 hover:bg-stone-100 transition-colors cursor-pointer"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>

                    {/* Days of Week Header */}
                    <div className="grid grid-cols-7 gap-1 text-center mb-1">
                      {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((d) => (
                        <div key={d} className="text-[11px] font-bold text-stone-400 py-1">
                          {d}
                        </div>
                      ))}
                    </div>

                    {/* Calendar Month Grid */}
                    <div className="grid grid-cols-7 gap-1 text-center">
                      {/* Empty offset days */}
                      {Array.from({ length: firstDayIndex }).map((_, idx) => (
                        <div key={`empty-${idx}`} className="h-8 w-8 mx-auto" />
                      ))}

                      {/* Days of the month */}
                      {Array.from({ length: daysInMonth }).map((_, idx) => {
                        const day = idx + 1;
                        const isPast = isPastDate(day);
                        const isStart = isSelectedStart(day);
                        const isEnd = isSelectedEnd(day);
                        const inRange = isInRange(day);

                        if (isPast) {
                          return (
                            <button
                              key={day}
                              type="button"
                              disabled
                              className="h-8 w-8 mx-auto text-xs text-stone-300 font-normal flex items-center justify-center cursor-not-allowed"
                            >
                              {day}
                            </button>
                          );
                        }

                        let dayClasses = "h-8 w-8 mx-auto text-xs font-medium flex items-center justify-center transition-all cursor-pointer ";
                        if (isStart && isEnd) {
                          dayClasses += "bg-[#1B4332] text-white font-bold rounded-xl shadow-xs ring-2 ring-[#1B4332]/30";
                        } else if (isStart) {
                          dayClasses += "bg-[#1B4332] text-white font-bold rounded-xl shadow-xs";
                        } else if (isEnd) {
                          dayClasses += "bg-[#1B4332] text-white font-bold rounded-xl shadow-xs";
                        } else if (inRange) {
                          dayClasses += "bg-emerald-100/80 text-emerald-950 font-bold rounded-lg";
                        } else {
                          dayClasses += "text-stone-700 hover:bg-emerald-50 hover:text-emerald-900 rounded-lg";
                        }

                        return (
                          <button
                            key={day}
                            type="button"
                            onClick={() => handleDateClick(day)}
                            className={dayClasses}
                          >
                            {day}
                          </button>
                        );
                      })}
                    </div>

                    {/* Quick Trip Duration Chips */}
                    <div className="mt-3.5 pt-3 border-t border-stone-100 flex items-center justify-between gap-1">
                      <span className="text-[11px] font-semibold text-stone-500">Duration:</span>
                      <div className="flex items-center gap-1">
                        {[3, 5, 7, 10, 14].map((d) => (
                          <button
                            key={d}
                            type="button"
                            onClick={() => handlePresetDays(d)}
                            className={`text-[10px] sm:text-[11px] px-2 py-0.5 rounded-md font-semibold transition-colors cursor-pointer ${
                              formState.days === d
                                ? "bg-[#1B4332] text-white"
                                : "bg-stone-100 text-stone-700 hover:bg-emerald-50 hover:text-emerald-900"
                            }`}
                          >
                            {d}d
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Footer: Summary and Done */}
                    <div className="mt-3 pt-2.5 border-t border-stone-100 flex items-center justify-between">
                      <div className="text-[11px] text-stone-700 font-medium">
                        <span className="font-bold text-[#1B4332]">{formState.days} Days</span>
                        <span className="text-stone-400 mx-1">•</span>
                        <span>{formState.startDate} → {formState.endDate}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => setIsDatePickerOpen(false)}
                        className="px-3 py-1 bg-[#1B4332] hover:bg-[#143326] text-white text-xs font-bold rounded-lg transition-colors cursor-pointer"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                )}
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
