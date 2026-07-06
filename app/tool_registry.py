from app.tools.weather import WeatherTool
from app.tools.currency import CurrencyTool
from app.tools.places import PlacesTool
from app.tools.flights import FlightTool
from app.tools.hotels import HotelTool
from app.tools.maps import MapsTool


weather_tool = WeatherTool()
currency_tool = CurrencyTool()
places_tool = PlacesTool()
flight_tool = FlightTool()
hotel_tool = HotelTool()
maps_tool = MapsTool()


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": (
                "Get the current weather information for a given city."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "The name of the city for which weather "
                            "information is required."
                        ),
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": (
                "Convert money from one currency to another."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert."
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code (e.g. USD)."
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code (e.g. INR)."
                    }
                },
                "required": [
                    "amount",
                    "from_currency",
                    "to_currency"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_places",
            "description": (
                "Search for places such as restaurants, hotels, "
                "cafes, museums, airports, hospitals, tourist "
                "attractions, shopping malls, bus stations, and "
                "train stations in a city."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": (
                            "City in which to search."
                        ),
                    },
                    "category": {
                        "type": "string",
                        "description": (
                            "Place category such as restaurant, "
                            "hotel, cafe, museum, airport, "
                            "hospital, tourist_attraction, "
                            "shopping_mall, bus_station, "
                            "or train_station."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of places to return."
                        ),
                        "default": 5,
                    },
                },
                "required": [
                    "city",
                    "category",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": (
                "Search flights between two airports using their "
                "IATA airport codes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "departure_iata": {
                        "type": "string",
                        "description": (
                            "Departure airport IATA code "
                            "(e.g. DEL, CCU, BOM)."
                        ),
                    },
                    "arrival_iata": {
                        "type": "string",
                        "description": (
                            "Arrival airport IATA code "
                            "(e.g. BOM, BLR, HYD)."
                        ),
                    },
                    "flight_number": {
                        "type": "string",
                        "description": (
                            "Optional flight number."
                        ),
                    },
                    "airline_iata": {
                        "type": "string",
                        "description": (
                            "Optional airline IATA code."
                        ),
                    },
                    "flight_date": {
                        "type": "string",
                        "description": (
                            "Optional flight date in YYYY-MM-DD format."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of flights to return."
                        ),
                        "default": 10,
                    },
                },
                "required": [
                    "departure_iata",
                    "arrival_iata",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": (
                "Search for hotels in a given city."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City in which to search for hotels."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of hotels to return.",
                        "default": 5,
                    },
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_route",
            "description": (
                "Calculate the best route between two places."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "Starting location."
                        ),
                    },
                    "destination": {
                        "type": "string",
                        "description": (
                            "Destination location."
                        ),
                    },
                    "mode": {
                        "type": "string",
                        "description": (
                            "Travel mode: drive, walk or bicycle."
                        ),
                        "default": "drive",
                    },
                },
                "required": [
                    "origin",
                    "destination",
                ],
            },
        },
    },
]


AVAILABLE_TOOLS = {
    "get_current_weather": weather_tool.get_current_weather,
    "convert_currency": currency_tool.convert_currency,
    "search_places": places_tool.search_places,
    "search_flights": flight_tool.search_flights,
    "search_hotels": hotel_tool.search_hotels,
    "get_route": maps_tool.get_route,
}