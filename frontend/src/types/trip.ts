export interface FlightJourney {
  route: string;
  departure: string;
  arrival: string;
  flight_number?: string | null;
  stops: number;
  airline?: string | null;
}

export interface FlightSegmentDetail {
  carrier?: string;
  carrier_code?: string;
  flight_number?: string;
  aircraft?: string;
  origin?: string;
  destination?: string;
  departure_time?: string;
  departure_date?: string;
  arrival_time?: string;
  arrival_date?: string;
  duration_minutes?: number;
}

export interface FlightOption {
  id?: string;
  airline: string;
  airline_code?: string;
  flight_number?: string;
  flight_numbers?: string[];
  origin: string;
  destination: string;
  departure_date: string;
  departure_time: string;
  arrival_date: string;
  arrival_time: string;
  duration?: string;
  duration_formatted?: string;
  total_duration_minutes?: number;
  stops: number;
  price: number;
  currency: string;
  baggage?: string;
  cabin_baggage?: string;
  checked_baggage?: string;
  booking_url?: string;
  is_round_trip?: boolean;
  is_direct?: boolean;
  is_lowest_price?: boolean;
  direction?: "outbound" | "return";
  journey_label?: string;
  segments?: FlightSegmentDetail[];
  outbound_journey?: FlightJourney;
  return_journey?: FlightJourney;
  provider?: string;
  verified_status?: string;
}

export interface HotelNearbyPlace {
  name?: string;
  transportations?: Array<{
    type?: string;
    duration?: string;
  }>;
}

export interface HotelPriceItem {
  source?: string;
  rate_per_night?: number | string;
  total_rate?: number | string;
  official?: boolean;
}

export interface HotelOption {
  id?: string;
  property_name: string;
  name?: string;
  destination_city: string;
  address: string;
  hotel_class?: number | string;
  rating?: number;
  reviews?: number;
  reviews_count?: number;
  location_rating?: number;
  property_type?: string;
  price_per_night?: number | string;
  rate_per_night?: number | string;
  total_price?: number | string;
  total_rate?: number | string;
  currency: string;
  live_rates_available: boolean;
  is_lowest_price?: boolean;
  pricing_notice?: string;
  recommended_rooms?: string;
  room_guidance?: string;
  check_in_date?: string;
  check_out_date?: string;
  check_in_time?: string;
  check_out_time?: string;
  nights?: number;
  booking_url?: string;
  image_url?: string;
  amenities?: string[];
  excluded_amenities?: string[];
  nearby_places?: HotelNearbyPlace[];
  essential_info?: string[];
  prices?: HotelPriceItem[];
}

export interface RouteDetail {
  origin: string;
  destination: string;
  distance_km: number;
  duration_text: string;
  highway?: string;
  key_stops?: string[];
}

export interface DailyWeatherForecast {
  date: string;
  day_number?: number;
  day_name?: string;
  formatted_date?: string;
  temp_max_c: number;
  temp_min_c: number;
  temp_avg_c?: number;
  condition: string;
  precipitation_probability?: number;
  humidity?: number;
  feels_like_c?: number;
  recommendation?: string;
  forecast_type?: string;
}

export interface WeatherInfo {
  city: string;
  region?: string;
  country?: string;
  start_date?: string;
  end_date?: string;
  duration_days?: number;
  temperature_c?: number;
  condition?: string;
  humidity?: number;
  feels_like_c?: number;
  overall_high_c?: number;
  overall_low_c?: number;
  observation_timestamp?: string;
  classification?: string;
  forecast_summary?: string;
  daily_forecast?: DailyWeatherForecast[];
}

export interface ItineraryActivity {
  time: "Morning" | "Afternoon" | "Evening";
  title: string;
  description: string;
  tag?: string;
}

export interface ItineraryTransit {
  from: string;
  to: string;
  mode: string;
  distance?: string;
  duration?: string;
}

export interface ItineraryDay {
  day: number;
  date: string;
  destination: string;
  title: string;
  summary: string;
  activities: ItineraryActivity[];
  transit?: ItineraryTransit | null;
  weather?: {
    temp_range?: string;
    condition?: string;
    recommendation?: string;
  } | null;
}

export interface BudgetCategory {
  name: string;
  amount: number;
  percentage: number;
  color: string;
  notes?: string;
}

export interface BudgetSummary {
  user_budget: number;
  estimated_total: number;
  currency: string;
  currency_symbol: string;
  difference: number;
  is_within_budget: boolean;
  status_label: string;
  status_color: string;
  categories: BudgetCategory[];
}

export interface LatencyBreakdown {
  total_latency_ms: number;
  total_latency_sec: number;
  formatted: string;
  stages?: Record<string, number>;
  tools?: Record<string, number>;
  concurrency_speedup?: string;
}

export interface TripData {
  trip_id: string;
  title: string;
  destination_summary: string;
  destinations: string[];
  travel_dates: {
    start: string;
    end: string;
    duration_days: number;
    formatted: string;
  };
  travelers: {
    count: number;
    label: string;
  };
  status: string;
  overview: string;
  itinerary: ItineraryDay[];
  trip_type?: "roundtrip" | "oneway";
  flights: FlightOption[];
  outbound_flights?: FlightOption[];
  return_flights?: FlightOption[];
  hotels: HotelOption[];
  routes: RouteDetail[];
  weather: WeatherInfo[];
  attractions?: AttractionItem[];
  budget: BudgetSummary;
  raw_sections?: Record<string, string>;
  final_response?: string;
  latency?: LatencyBreakdown;
}

export interface AttractionItem {
  name: string;
  rating?: number | string;
  categories?: string[];
  category?: string;
  description?: string;
  address?: string;
  formatted_address?: string;
  city?: string;
  provider?: string;
  image?: string;
  photo_url?: string;
  lat?: number;
  lon?: number;
  website?: string;
}

export interface ProgressEventPayload {
  task_id: number | string;
  description: string;
  status: "pending" | "ready" | "running" | "completed" | "failed";
  worker_id?: number | null;
  execution_time?: number | null;
  error?: string | null;
}

export type ActiveTabType = "overview" | "itinerary" | "flights" | "hotels" | "budget";

