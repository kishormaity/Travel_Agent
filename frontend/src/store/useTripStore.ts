import { create } from "zustand";
import { TripData, ActiveTabType, ProgressEventPayload } from "../types/trip";
import { mockKeralaTrip } from "../data/mockKeralaTrip";
import { planTripWithApi } from "../lib/api";

export interface TripFormState {
  destination: string;
  origin: string;
  dates: string;
  startDate: string;
  endDate: string;
  days: number;
  travelers: number;
  adults: number;
  children: number;
  infants: number;
  cabinClass: "ECONOMY" | "PREMIUM_ECONOMY" | "BUSINESS" | "FIRST";
  maxStops: "ANY" | "NON_STOP" | "ONE_STOP" | "TWO_PLUS_STOPS";
  budget: number;
  currency: string;
  tripType: "roundtrip" | "oneway";
}

interface TripStoreState {
  trip: TripData | null;
  activeTab: ActiveTabType;
  isLoading: boolean;
  progressEvents: ProgressEventPayload[];
  currentProgressMessage: string;
  formState: TripFormState;
  hasGeneratedTrip: boolean;

  // Actions
  setActiveTab: (tab: ActiveTabType) => void;
  updateFormState: (updates: Partial<TripFormState>) => void;
  planTrip: () => Promise<void>;
  resetToMock: () => void;
}

export const useTripStore = create<TripStoreState>((set, get) => ({
  trip: null,
  activeTab: "overview",
  isLoading: false,
  progressEvents: [],
  currentProgressMessage: "",
  hasGeneratedTrip: false,
  formState: {
    destination: "",
    origin: "Delhi (DEL)",
    dates: "2026-11-20 – 2026-11-27",
    startDate: "2026-11-20",
    endDate: "2026-11-27",
    days: 7,
    travelers: 1,
    adults: 1,
    children: 0,
    infants: 0,
    cabinClass: "ECONOMY",
    maxStops: "ANY",
    budget: 90000,
    currency: "INR",
    tripType: "roundtrip",
  },

  setActiveTab: (tab: ActiveTabType) => {
    set({ activeTab: tab });
  },

  updateFormState: (updates: Partial<TripFormState>) => {
    set((state) => ({
      formState: { ...state.formState, ...updates },
    }));
  },

  resetToMock: () => {
    set({
      trip: null,
      hasGeneratedTrip: false,
      activeTab: "overview",
      isLoading: false,
      progressEvents: [],
    });
  },

  planTrip: async () => {
    const { formState } = get();
    set({
      isLoading: true,
      progressEvents: [],
      currentProgressMessage: `Planning trip to ${formState.destination}...`,
    });

    try {
      let days = formState.days || 7;
      const matchDays = formState.dates.match(/(\d+)\s*days?/i);
      if (matchDays) {
        days = parseInt(matchDays[1], 10);
      }

      const totalTravelers = (formState.adults || 1) + (formState.children || 0) + (formState.infants || 0);
      const result = await planTripWithApi(
        {
          destination: formState.destination,
          origin: formState.origin,
          startDate: formState.startDate,
          endDate: formState.tripType === "roundtrip" ? formState.endDate : undefined,
          days: days,
          travelers: totalTravelers,
          adults: formState.adults,
          children: formState.children,
          infants: formState.infants,
          cabinClass: formState.cabinClass,
          maxStops: formState.maxStops,
          budget: formState.budget,
          currency: formState.currency,
          tripType: formState.tripType,
        },
        (evt) => {
          set((prev) => ({
            currentProgressMessage: evt.description,
            progressEvents: [...prev.progressEvents, evt],
          }));
        }
      );

      // Set fresh state reference guaranteed to trigger React re-render
      set({
        trip: { ...result },
        hasGeneratedTrip: true,
        isLoading: false,
        activeTab: "overview",
      });

      // Smooth scroll down to workspace
      setTimeout(() => {
        const workspaceEl = document.getElementById("trip-workspace");
        if (workspaceEl) {
          workspaceEl.scrollIntoView({ behavior: "smooth" });
        }
      }, 50);
    } catch (error) {
      console.error("Error planning trip:", error);
      set({
        isLoading: false,
        currentProgressMessage: "Failed to generate plan. Please try again.",
      });
    }
  },
}));
