from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional

# Weather API response validation models
class WeatherLocation(BaseModel):
    name: str
    region: str
    country: str
    lat: float
    lon: float
    localtime: str

class WeatherCondition(BaseModel):
    text: str

class CurrentWeather(BaseModel):
    temp_c: float
    temp_f: float
    condition: WeatherCondition
    humidity: int
    wind_kph: float
    wind_dir: str
    feelslike_c: float
    vis_km: float
    uv: float

class WeatherResponseModel(BaseModel):
    location: WeatherLocation
    current: CurrentWeather


# Flight API (AviationStack) response validation models
class FlightAirline(BaseModel):
    name: Optional[str] = None

class FlightDetail(BaseModel):
    number: Optional[str] = None
    iata: Optional[str] = None
    icao: Optional[str] = None

class FlightAirportInfo(BaseModel):
    airport: Optional[str] = None
    iata: Optional[str] = None
    terminal: Optional[str] = None
    gate: Optional[str] = None
    scheduled: Optional[str] = None

class FlightItem(BaseModel):
    airline: Optional[FlightAirline] = None
    flight: Optional[FlightDetail] = None
    departure: Optional[FlightAirportInfo] = None
    arrival: Optional[FlightAirportInfo] = None
    flight_status: Optional[str] = None

class FlightResponseModel(BaseModel):
    data: List[FlightItem] = []


# Places API (Geoapify) response validation models
class PlaceProperties(BaseModel):
    name: Optional[str] = None
    formatted: Optional[str] = None
    lat: float
    lon: float
    categories: List[str] = []

class PlaceFeature(BaseModel):
    properties: PlaceProperties

class PlacesResponseModel(BaseModel):
    features: List[PlaceFeature] = []


# Maps / Routing API (Geoapify) response validation models
class MapsStep(BaseModel):
    instruction: Optional[str] = None
    distance: Optional[float] = None

class MapsLeg(BaseModel):
    steps: List[MapsStep] = []

class MapsProperties(BaseModel):
    distance: float
    time: float
    legs: List[MapsLeg] = []

class MapsFeature(BaseModel):
    properties: MapsProperties

class MapsResponseModel(BaseModel):
    features: List[MapsFeature] = []


# Geocoding API (Geoapify) response validation models
class GeocodingTimezone(BaseModel):
    name: Optional[str] = None

class GeocodingProperties(BaseModel):
    place_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    postcode: Optional[str] = None
    formatted: Optional[str] = None
    lat: float
    lon: float
    timezone: Optional[GeocodingTimezone] = None

class GeocodingFeature(BaseModel):
    properties: GeocodingProperties

class GeocodingResponseModel(BaseModel):
    features: List[GeocodingFeature] = []


# Currency API (Frankfurter) response validation models
class CurrencyResponseModel(BaseModel):
    amount: float
    base: str
    rates: Dict[str, float]
    date: str
