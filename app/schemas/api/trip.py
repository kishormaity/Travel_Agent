from pydantic import BaseModel, Field

class TripRequest(BaseModel):
    """
    User's travel preferences.
    """
    destination: str
    budget: float
    days: int
    travelers: int = 1


class BudgetEstimate(BaseModel):
    """
    Estimated trip budget.
    """
    hotel_cost: float
    food_cost: float
    transport_cost: float
    miscellaneous_cost: float
    total_cost: float


class Itinerary(BaseModel):
    """
    Daily travel itinerary.
    """
    day: int
    activity: str