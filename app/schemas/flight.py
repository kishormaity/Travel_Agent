from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FlightSegment(BaseModel):
    """Represents an individual leg or flight segment."""
    carrier: str
    carrier_code: Optional[str] = None
    flight_number: Optional[str] = None
    aircraft: Optional[str] = None
    origin: str  # IATA
    destination: str  # IATA
    departure_time: str
    departure_date: Optional[str] = None
    departure_timezone: Optional[str] = None  # None if provider did not specify
    arrival_time: str
    arrival_date: Optional[str] = None
    arrival_timezone: Optional[str] = None  # None if provider did not specify
    duration_minutes: Optional[int] = None


class FlightLayover(BaseModel):
    """Represents a connection layover between segments."""
    airport: str  # IATA
    duration_minutes: Optional[int] = None
    duration_seconds: Optional[int] = None


class NormalizedFlightOffer(BaseModel):
    """Normalized flight offer representation preserving provider attribution and metadata."""
    provider: str = "flight_octotrip"
    provider_flight_id: Optional[str] = None
    airline: str
    airline_code: Optional[str] = None
    flight_number: Optional[str] = None  # primary flight number for compatibility
    flight_numbers: List[str] = Field(default_factory=list)
    origin: str  # IATA
    destination: str  # IATA
    departure_time: str
    departure_date: Optional[str] = None
    departure_timezone: Optional[str] = None
    arrival_time: str
    arrival_date: Optional[str] = None
    arrival_timezone: Optional[str] = None
    is_direct: bool = True
    stops: int = 0
    is_round_trip: bool = False
    is_overnight: bool = False
    date_change_days: int = 0
    segments: List[FlightSegment] = Field(default_factory=list)
    layovers: List[FlightLayover] = Field(default_factory=list)
    inbound_segments: List[FlightSegment] = Field(default_factory=list)
    inbound_layovers: List[FlightLayover] = Field(default_factory=list)
    outbound_duration_minutes: Optional[int] = None
    inbound_duration_minutes: Optional[int] = None
    outbound_duration_formatted: str = ""
    inbound_duration_formatted: str = ""
    outbound_airline: Optional[str] = None
    inbound_airline: Optional[str] = None
    return_origin: Optional[str] = None
    return_destination: Optional[str] = None
    return_departure_time: Optional[str] = None
    return_departure_date: Optional[str] = None
    return_arrival_time: Optional[str] = None
    return_arrival_date: Optional[str] = None
    outbound_stops: int = 0
    inbound_stops: int = 0
    total_stops: int = 0
    total_round_trip_price: Optional[float] = None
    route_match: bool = True
    airport_notes: Optional[str] = None
    duration_formatted: str = ""
    total_duration_minutes: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = "INR"
    fare_type: Optional[str] = None
    baggage: Optional[str] = None
    cabin_baggage: Optional[str] = None
    checked_baggage: Optional[str] = None
    outbound_baggage: Optional[str] = None
    inbound_baggage: Optional[str] = None
    outbound_cabin_baggage: Optional[str] = None
    outbound_checked_baggage: Optional[str] = None
    inbound_cabin_baggage: Optional[str] = None
    inbound_checked_baggage: Optional[str] = None
    passenger_count: Optional[int] = 1
    adults: int = 1
    children: int = 0
    infants: int = 0
    booking_url: Optional[str] = None
    is_bookable: bool = False
    price_verification_timestamp: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    rankings: Dict[str, int] = Field(default_factory=dict)
    best_value_score: Optional[float] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
