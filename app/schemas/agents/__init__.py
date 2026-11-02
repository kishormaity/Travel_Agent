from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaseAgentOutput(BaseModel):
    """Standardized envelope for output returned by any specialized agent."""
    agent_name: str
    success: bool
    summary: str
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class FlightAgentOutput(BaseAgentOutput):
    agent_name: str = "flight_agent"
    flights: List[Dict[str, Any]] = Field(default_factory=list)


class AccommodationAgentOutput(BaseAgentOutput):
    agent_name: str = "accommodation_agent"
    accommodations: List[Dict[str, Any]] = Field(default_factory=list)


class DestinationAgentOutput(BaseAgentOutput):
    agent_name: str = "destination_agent"
    attractions: List[Dict[str, Any]] = Field(default_factory=list)
    location_details: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = None


class WeatherAgentOutput(BaseAgentOutput):
    agent_name: str = "weather_agent"
    forecast: Optional[Dict[str, Any]] = None
    advisory: Optional[str] = None
    historical_climate: Optional[Dict[str, Any]] = None
    daily_statuses: List[Dict[str, Any]] = Field(default_factory=list)
    is_forecast_available: bool = True
    limitation_note: Optional[str] = None


class BudgetAgentOutput(BaseAgentOutput):
    agent_name: str = "budget_agent"
    currency_conversions: List[Dict[str, Any]] = Field(default_factory=list)
    budget_breakdown: Optional[Dict[str, Any]] = None
    estimated_total: Optional[float] = None


class RouteAgentOutput(BaseAgentOutput):
    agent_name: str = "route_agent"
    routes: List[Dict[str, Any]] = Field(default_factory=list)
    transit_recommendation: Optional[str] = None


class SynthesizerAgentOutput(BaseAgentOutput):
    agent_name: str = "synthesizer_agent"
    itinerary_markdown: str = ""
    completeness_score: float = 1.0
    missing_aspects: List[str] = Field(default_factory=list)
