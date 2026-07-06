from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    User message sent to the travel agent.
    """
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """
    AI response returned to the user.
    """
    response: str


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