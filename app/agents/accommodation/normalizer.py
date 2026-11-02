"""
Accommodation Normalizer for HasData Google Hotels and Fallback Providers.
Extracts verified property names, ratings, live rates, GPS coordinates, and booking URLs.
Ensures transparent data classification and prevents synthetic pricing or classifications.
"""

import json
from typing import Any, Dict, List, Optional
from loguru import logger


def extract_raw_json(data: Any) -> Any:
    """Extract and parse JSON content from MCP TextContent blocks, strings, or structured dicts."""
    if data is None:
        return None
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], dict) and "text" in data[0]:
            merged_results = []
            for block in data:
                text_content = block.get("text", "")
                if text_content:
                    try:
                        parsed = json.loads(text_content)
                        merged_results.append(parsed)
                    except Exception:
                        pass
            if len(merged_results) == 1:
                return merged_results[0]
            elif len(merged_results) > 1:
                return merged_results
        return data
    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            return data
    return data


def normalize_hasdata_property(
    prop: Dict[str, Any],
    city: str,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    adults: int = 2,
    rooms: Optional[int] = None,
    currency: Optional[str] = "INR",
) -> Dict[str, Any]:
    """Normalize a single HasData Google Hotels property dictionary into a unified schema."""
    name = prop.get("name") or f"Accommodation in {city}"
    hotel_class = prop.get("hotelClass") or prop.get("extractedHotelClass")
    rating = prop.get("overallRating")
    reviews = prop.get("reviews")

    # Rate parsing
    rate_per_night_obj = prop.get("ratePerNight") or {}
    total_rate_obj = prop.get("totalRate") or {}

    nightly_num = rate_per_night_obj.get("extractedLowest") if isinstance(rate_per_night_obj, dict) else None
    nightly_str = rate_per_night_obj.get("lowest") if isinstance(rate_per_night_obj, dict) else None

    total_num = total_rate_obj.get("extractedLowest") if isinstance(total_rate_obj, dict) else None
    total_str = total_rate_obj.get("lowest") if isinstance(total_rate_obj, dict) else None

    has_live_rates = bool(nightly_num or nightly_str or total_num or total_str)

    gps = prop.get("gpsCoordinates") or {}
    lat = gps.get("latitude") if isinstance(gps, dict) else None
    lon = gps.get("longitude") if isinstance(gps, dict) else None

    link = prop.get("link")

    rec_rooms = rooms if rooms else (1 if adults <= 2 else (2 if adults <= 4 else max(1, adults // 2)))

    pricing_notice = (
        "Verified live dynamic rate from Google Hotels."
        if has_live_rates
        else "Property discovered via Google Hotels; live rates not available for these dates, verify directly on booking sites."
    )

    return {
        "property_name": name,
        "name": name,
        "address": prop.get("description") or f"{name}, {city}",
        "city": city,
        "state": None,
        "country": "India",
        "latitude": lat,
        "longitude": lon,
        "hotel_class": hotel_class,
        "rating": rating,
        "reviews": reviews,
        "price_per_night": nightly_num or nightly_str,
        "price_per_night_formatted": nightly_str,
        "total_price": total_num or total_str,
        "total_price_formatted": total_str,
        "currency": currency,
        "booking_url": link,
        "data_source": "HasData (Google Hotels)",
        "live_rates_available": has_live_rates,
        "pricing_notice": pricing_notice,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": adults,
        "recommended_rooms": rec_rooms,
        "room_guidance": f"For {adults} adult(s), {rec_rooms} room(s) is typical. Do not assume {adults} separate rooms are needed.",
    }


def normalize_hasdata_hotel_results(
    raw_response: Any,
    city: str,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    adults: int = 2,
    rooms: Optional[int] = None,
    currency: Optional[str] = "INR",
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Parse raw HasData response and return normalized hotel dictionaries deduplicated by name."""
    data = extract_raw_json(raw_response)
    if not data or not isinstance(data, dict):
        return []

    json_body = data.get("json", {})
    if not isinstance(json_body, dict):
        return []

    properties = json_body.get("properties", [])
    if not properties or not isinstance(properties, list):
        return []

    normalized_hotels = []
    seen_names = set()

    for p in properties:
        if not isinstance(p, dict):
            continue
        norm = normalize_hasdata_property(
            p,
            city=city,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults,
            rooms=rooms,
            currency=currency,
        )
        name_key = norm["name"].strip().lower()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)
        normalized_hotels.append(norm)
        if len(normalized_hotels) >= limit:
            break

    logger.info(f"Normalized {len(normalized_hotels)} properties from HasData Google Hotels for '{city}'")
    return normalized_hotels
