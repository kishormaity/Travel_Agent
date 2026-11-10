"""
Accommodation Normalizer for HasData Google Hotels and Fallback Providers.
Extracts verified property names, ratings, live rates, GPS coordinates, and booking URLs.
Ensures transparent data classification and prevents synthetic pricing or classifications.
"""

import json
import re
from datetime import datetime
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
    """Normalize a single HasData Google Hotels property dictionary into a unified schema, preserving all non-null fields."""
    name = prop.get("name") or f"Accommodation in {city}"
    hotel_class = prop.get("hotelClass") or prop.get("extractedHotelClass")
    rating = prop.get("overallRating")
    reviews = prop.get("reviews")
    location_rating = prop.get("locationRating")
    property_type = prop.get("type")

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

    # Images extraction
    images_list = prop.get("images", [])
    first_image = None
    if images_list and isinstance(images_list, list) and len(images_list) > 0:
        if isinstance(images_list[0], dict):
            first_image = images_list[0].get("originalImage") or images_list[0].get("thumbnail")
        elif isinstance(images_list[0], str):
            first_image = images_list[0]

    # Calculate nights
    nights = 1
    if check_in_date and check_out_date:
        try:
            d1 = datetime.strptime(str(check_in_date).strip()[:10], "%Y-%m-%d")
            d2 = datetime.strptime(str(check_out_date).strip()[:10], "%Y-%m-%d")
            nights = max(1, (d2 - d1).days)
        except Exception:
            nights = 1

    pricing_notice = (
        "Verified live dynamic rate from Google Hotels."
        if has_live_rates
        else "Property discovered via Google Hotels; live rates not available for these dates, verify directly on booking sites."
    )

    return {
        "property_name": name,
        "name": name,
        "destination_city": city,
        "address": prop.get("description") or f"{name}, {city}",
        "city": city,
        "state": None,
        "country": "India",
        "latitude": lat,
        "longitude": lon,
        "hotel_class": hotel_class,
        "rating": rating,
        "reviews": reviews,
        "location_rating": location_rating,
        "property_type": property_type,
        "price_per_night": nightly_num or (float(re.sub(r"[^\d.]", "", nightly_str)) if nightly_str and re.sub(r"[^\d.]", "", nightly_str) else None),
        "price_per_night_formatted": nightly_str,
        "total_price": total_num or (float(re.sub(r"[^\d.]", "", total_str)) if total_str and re.sub(r"[^\d.]", "", total_str) else None),
        "total_price_formatted": total_str,
        "currency": currency or "INR",
        "booking_url": link,
        "image_url": first_image,
        "images": images_list if isinstance(images_list, list) else [],
        "amenities": prop.get("amenities") or [],
        "excluded_amenities": prop.get("excludedAmenities") or [],
        "essential_info": prop.get("essentialInfo") or [],
        "nearby_places": prop.get("nearbyPlaces") or [],
        "prices": prop.get("prices") or [],
        "check_in_time": prop.get("checkInTime"),
        "check_out_time": prop.get("checkOutTime"),
        "deals": prop.get("dealType") or prop.get("deals"),
        "data_source": "HasData (Google Hotels)",
        "live_rates_available": has_live_rates,
        "pricing_notice": pricing_notice,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "nights": nights,
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
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Parse raw HasData response and return all normalized hotel dictionaries sorted by lowest price first."""
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
        if limit is not None and len(normalized_hotels) >= limit:
            break

    # Sort hotels: lowest price first on top; unpriced stays placed at bottom
    def _rate_key(item: Dict[str, Any]) -> float:
        val = item.get("price_per_night") or item.get("total_price")
        if isinstance(val, (int, float)):
            return float(val) if float(val) > 0 else float("inf")
        if isinstance(val, str):
            clean = re.sub(r"[^\d.]", "", val)
            try:
                v = float(clean)
                return v if v > 0 else float("inf")
            except (ValueError, TypeError):
                return float("inf")
        return float("inf")

    normalized_hotels.sort(key=_rate_key)

    # Mark the lowest priced hotel
    if normalized_hotels:
        min_p = _rate_key(normalized_hotels[0])
        if min_p != float("inf"):
            for h in normalized_hotels:
                h["is_lowest_price"] = (_rate_key(h) == min_p)

    logger.info(f"Normalized {len(normalized_hotels)} properties from HasData Google Hotels for '{city}' (sorted by lowest price)")
    return normalized_hotels
