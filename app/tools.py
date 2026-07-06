from datetime import datetime


def get_current_time() -> str:
    """
    Returns the current date and time.
    """
    return datetime.now().strftime("%d %B %Y, %I:%M %p")


def calculate_trip_budget(
    hotel_per_night: float,
    number_of_nights: int,
    food_per_day: float,
    transport_cost: float,
    misc_cost: float = 0,
) -> float:
    """
    Calculate the estimated total trip cost.
    """
    hotel_cost = hotel_per_night * number_of_nights
    food_cost = food_per_day * number_of_nights

    total = hotel_cost + food_cost + transport_cost + misc_cost
    return round(total, 2)


def suggest_transport(distance_km: float) -> str:
    """
    Suggest a mode of transport based on distance.
    """
    if distance_km <= 5:
        return "🚶 Walking or Cycling"

    elif distance_km <= 100:
        return "🚗 Car or Bus"

    elif distance_km <= 500:
        return "🚆 Train"

    else:
        return "✈️ Flight"


def format_itinerary(days: int, destination: str) -> list[str]:
    """
    Create a simple itinerary template.
    """
    itinerary = []

    for day in range(1, days + 1):
        itinerary.append(
            f"Day {day}: Explore popular attractions in {destination}."
        )

    return itinerary