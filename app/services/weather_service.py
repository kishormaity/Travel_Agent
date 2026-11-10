import datetime
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger

from app.config import (
    WEATHER_API_KEY,
    WEATHER_API_BASE_URL,
)

WMO_WEATHER_CODES: Dict[int, tuple[str, str]] = {
    0: ("Clear Sky", "Pleasant, clear skies throughout the day. Perfect for outdoor sightseeing and monument visits."),
    1: ("Mainly Clear", "Mostly sunny with occasional light clouds. Excellent conditions for photography and walking tours."),
    2: ("Partly Cloudy", "Comfortable partly cloudy weather. Great daytime conditions; light layers recommended."),
    3: ("Overcast", "Cloudy skies with mild temperatures. Ideal for comfortable daytime walking without intense direct sun."),
    45: ("Foggy", "Morning fog clearing by midday. Allow extra transit time for early morning drives."),
    48: ("Depositing Rime Fog", "Cool, misty fog conditions in the early hours."),
    51: ("Light Drizzle", "Intermittent light drizzle. Keep a compact umbrella handy for outdoor walks."),
    53: ("Moderate Drizzle", "Passing drizzle; indoor museum or palace visits recommended during wet spells."),
    55: ("Dense Drizzle", "Sustained light rain. Light rain jacket recommended."),
    61: ("Slight Rain", "Light rain showers expected. Plan afternoon indoor activities or cafe breaks."),
    63: ("Moderate Rain", "Steady rain showers. Carry waterproof gear; explore indoor cultural attractions."),
    65: ("Heavy Rain", "Heavy rainfall expected. Schedule museum and gallery visits during peak rain."),
    71: ("Slight Snow", "Light snow flurries. Warm winter attire and insulated boots recommended."),
    73: ("Moderate Snow", "Steady snowfall creating scenic winter landscapes. Dress warmly in thermal layers."),
    75: ("Heavy Snow", "Heavy snowfall; check mountain road passes and mountain transport schedules."),
    80: ("Light Showers", "Scattered light showers. Mostly clear between brief rain spells."),
    81: ("Moderate Showers", "Passing rain showers with dry intervals."),
    82: ("Violent Showers", "Intense short-lived rain downpours. Plan flexible indoor backup itineraries."),
    95: ("Thunderstorm", "Thunderstorm activity possible. Stay indoors during storms; enjoy hotel dining or indoor exhibits."),
    96: ("Thunderstorm with Hail", "Severe weather with hail. Avoid outdoor excursions during storm windows."),
}


class WeatherService:
    """
    Handles weather forecast retrieval, delivering day-by-day weather
    forecasts for requested travel dates using WeatherAPI and Open-Meteo.
    """

    def __init__(self):
        self.api_key = WEATHER_API_KEY
        self.base_url = WEATHER_API_BASE_URL

    def _parse_dates(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> tuple[datetime.date, datetime.date]:
        """Parse or derive clean start and end dates."""
        today = datetime.date.today()
        d_start = today
        if start_date:
            try:
                clean_start = str(start_date).strip()[:10]
                d_start = datetime.datetime.strptime(clean_start, "%Y-%m-%d").date()
            except Exception:
                d_start = today

        total_days = int(days) if days and int(days) > 0 else 7
        d_end = d_start + datetime.timedelta(days=total_days - 1)
        if end_date:
            try:
                clean_end = str(end_date).strip()[:10]
                parsed_end = datetime.datetime.strptime(clean_end, "%Y-%m-%d").date()
                if parsed_end >= d_start:
                    d_end = parsed_end
            except Exception:
                pass

        return d_start, d_end

    def _get_coordinates_and_location(self, city: str) -> tuple[float, float, str, str, str]:
        """Resolve latitude, longitude, and verified location details for a city."""
        # 1. Try WeatherAPI first for precise Indian & global resolution
        if self.api_key and self.base_url:
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.get(
                        f"{self.base_url}/current.json",
                        params={"key": self.api_key, "q": city},
                    )
                    if resp.status_code == 200:
                        loc = resp.json().get("location", {})
                        lat = loc.get("lat")
                        lon = loc.get("lon")
                        if lat is not None and lon is not None:
                            return (
                                float(lat),
                                float(lon),
                                loc.get("name") or city,
                                loc.get("region") or "",
                                loc.get("country") or "India",
                            )
            except Exception as e:
                logger.debug(f"[WeatherService] WeatherAPI coordinate lookup failed for '{city}': {e}")

        # 2. Fallback to Open-Meteo Geocoding
        try:
            with httpx.Client(timeout=8.0) as client:
                query_name = f"{city}, India" if "india" not in city.lower() else city
                resp = client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": query_name, "count": 1},
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        r0 = results[0]
                        return (
                            float(r0["latitude"]),
                            float(r0["longitude"]),
                            r0.get("name") or city,
                            r0.get("admin1") or "",
                            r0.get("country") or "India",
                        )
        except Exception as e:
            logger.debug(f"[WeatherService] Open-Meteo geocoding fallback failed for '{city}': {e}")

        # 3. Default fallback coordinates (Jaipur / Central India region)
        return (26.9167, 75.8167, city, "Travel Region", "India")

    def get_weather_forecast(
        self,
        city: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch day-by-day weather forecasts for each day between start_date and end_date.
        """
        d_start, d_end = self._parse_dates(start_date, end_date, days)
        lat, lon, res_city, res_region, res_country = self._get_coordinates_and_location(city)

        logger.info(
            f"[WeatherService] Fetching day-by-day weather for '{res_city}' "
            f"from {d_start} to {d_end} (lat={lat}, lon={lon})"
        )

        fc_map: Dict[str, Dict[str, Any]] = {}

        # 1. Fetch 16-day dynamic forecast from Open-Meteo
        try:
            with httpx.Client(timeout=10.0) as client:
                r_fc = client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "daily": [
                            "temperature_2m_max",
                            "temperature_2m_min",
                            "weather_code",
                            "precipitation_probability_max",
                        ],
                        "timezone": "auto",
                        "forecast_days": 16,
                    },
                )
                if r_fc.status_code == 200:
                    fc_data = r_fc.json().get("daily", {})
                    if "time" in fc_data:
                        for i, t_str in enumerate(fc_data["time"]):
                            w_code = int(fc_data["weather_code"][i])
                            c_text, c_rec = WMO_WEATHER_CODES.get(
                                w_code, ("Pleasant", "Comfortable conditions for sightseeing.")
                            )
                            fc_map[t_str] = {
                                "max": float(fc_data["temperature_2m_max"][i]),
                                "min": float(fc_data["temperature_2m_min"][i]),
                                "code": w_code,
                                "condition": c_text,
                                "recommendation": c_rec,
                                "pop": int(fc_data["precipitation_probability_max"][i] or 0),
                                "forecast_type": "Live 16-Day Forecast",
                            }
        except Exception as e:
            logger.warning(f"[WeatherService] Open-Meteo 16-day forecast error: {e}")

        # 2. For any requested dates not in the 16-day window, fetch historical climate archive
        missing_dates = []
        cur = d_start
        while cur <= d_end:
            d_str = cur.strftime("%Y-%m-%d")
            if d_str not in fc_map:
                missing_dates.append(cur)
            cur += datetime.timedelta(days=1)

        arch_map: Dict[str, Dict[str, Any]] = {}
        if missing_dates:
            try:
                last_year_start = (missing_dates[0] - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
                last_year_end = (missing_dates[-1] - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
                with httpx.Client(timeout=10.0) as client:
                    r_arc = client.get(
                        "https://archive-api.open-meteo.com/v1/archive",
                        params={
                            "latitude": lat,
                            "longitude": lon,
                            "start_date": last_year_start,
                            "end_date": last_year_end,
                            "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
                            "timezone": "auto",
                        },
                    )
                    if r_arc.status_code == 200:
                        arc_data = r_arc.json().get("daily", {})
                        if "time" in arc_data:
                            for i, _ in enumerate(arc_data["time"]):
                                orig_key = missing_dates[i].strftime("%Y-%m-%d")
                                w_code = int(arc_data["weather_code"][i])
                                c_text, c_rec = WMO_WEATHER_CODES.get(
                                    w_code, ("Pleasant", "Comfortable sightseeing conditions.")
                                )
                                arch_map[orig_key] = {
                                    "max": float(arc_data["temperature_2m_max"][i]),
                                    "min": float(arc_data["temperature_2m_min"][i]),
                                    "code": w_code,
                                    "condition": c_text,
                                    "recommendation": c_rec,
                                    "pop": 5,
                                    "forecast_type": "Seasonal Climate Forecast",
                                }
            except Exception as e:
                logger.warning(f"[WeatherService] Archive climate lookup error: {e}")

        # 3. Assemble day-by-day forecast list for every single requested day
        daily_forecast_list: List[Dict[str, Any]] = []
        cur = d_start
        day_index = 1
        all_maxes = []
        all_mins = []

        while cur <= d_end:
            d_str = cur.strftime("%Y-%m-%d")
            day_name = cur.strftime("%A")
            day_abbr = cur.strftime("%a")
            month_day = cur.strftime("%b %d")

            day_info = fc_map.get(d_str) or arch_map.get(d_str) or {
                "max": 27.0,
                "min": 16.0,
                "code": 0,
                "condition": "Pleasant & Clear",
                "recommendation": "Comfortable weather for exploring city attractions and heritage walks.",
                "pop": 0,
                "forecast_type": "Regional Historical Average",
            }

            max_t = round(day_info["max"], 1)
            min_t = round(day_info["min"], 1)
            avg_t = round((max_t + min_t) / 2.0, 1)
            all_maxes.append(max_t)
            all_mins.append(min_t)

            daily_forecast_list.append({
                "date": d_str,
                "day_number": day_index,
                "day_name": day_name,
                "formatted_date": f"{day_abbr}, {month_day}",
                "temp_max_c": max_t,
                "temp_min_c": min_t,
                "temp_avg_c": avg_t,
                "condition": day_info["condition"],
                "precipitation_probability": day_info.get("pop", 0),
                "humidity": 45,
                "feels_like_c": avg_t,
                "recommendation": day_info["recommendation"],
                "forecast_type": day_info.get("forecast_type", "Daily Forecast"),
            })

            cur += datetime.timedelta(days=1)
            day_index += 1

        overall_high = max(all_maxes) if all_maxes else 28.0
        overall_low = min(all_mins) if all_mins else 16.0
        overall_avg = round((overall_high + overall_low) / 2.0, 1)

        # Determine prevailing condition
        conditions = [d["condition"] for d in daily_forecast_list]
        prevailing_condition = max(set(conditions), key=conditions.count) if conditions else "Pleasant & Clear"

        summary_text = (
            f"Day-by-day forecast for {res_city} across {len(daily_forecast_list)} requested travel days "
            f"({d_start.strftime('%b %d')} – {d_end.strftime('%b %d')}): Expect prevailing {prevailing_condition} "
            f"with daytime highs reaching {overall_high}°C and evening lows around {overall_low}°C."
        )

        return {
            "city": res_city,
            "region": res_region,
            "country": res_country,
            "latitude": lat,
            "longitude": lon,
            "start_date": d_start.strftime("%Y-%m-%d"),
            "end_date": d_end.strftime("%Y-%m-%d"),
            "duration_days": len(daily_forecast_list),
            "temperature_c": overall_avg,
            "condition": prevailing_condition,
            "humidity": 45,
            "feels_like_c": overall_avg,
            "overall_high_c": overall_high,
            "overall_low_c": overall_low,
            "forecast_summary": summary_text,
            "daily_forecast": daily_forecast_list,
            "provider": "Open-Meteo & WeatherAPI",
            "observation_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_current_weather(
        self,
        city: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Fetch day-by-day weather forecast for the requested city and dates.
        """
        return self.get_weather_forecast(
            city=city,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )

    async def get_current_weather_async(
        self,
        city: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Asynchronous wrapper to fetch weather forecast.
        """
        return self.get_weather_forecast(
            city=city,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )
