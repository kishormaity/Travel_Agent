from typing import Optional, List, Dict, Any
from loguru import logger
from langchain_core.tools import tool
from app.services.places_service import PlacesService
from app.schemas.tool_result import ToolResult
from app.core.cache import places_cache

_places_service = PlacesService()


def format_places_cli_table(places: List[Dict[str, Any]], city: str, provider: Optional[str] = None) -> str:
    """Format discovered famous attractions into a clean, human-readable list with 5-star ratings and provider details for the CLI terminal."""
    if not provider and places:
        first_src = places[0].get("data_source") or places[0].get("provider")
        if first_src == "apify_mcp" or "apify" in str(first_src).lower():
            provider = "Apify MCP Server (happitap/city-tourism-attractions-finder) [Primary]"
        else:
            provider = "Geoapify Places API (Fallback from Apify MCP)"
    if not provider:
        provider = "Geoapify Places API (Fallback from Apify MCP)"

    avg_rating = sum(float(p.get("rating", 5.0)) for p in places) / len(places) if places else 5.0
    rating_label = "Rated 5.0/5 ⭐" if all(float(p.get("rating", 5.0)) == 5.0 for p in places) else f"Top Rated (avg {avg_rating:.1f}/5 ⭐)"
    lines = [
        f"📍 [DESTINATION ATTRACTIONS & FAMOUS PLACES] -> {city.upper()} ({len(places)} Famous Landmarks · {rating_label})",
        f"🔌 Source Provider / MCP: {provider}",
        f"{'-' * 80}",
    ]
    for idx, p in enumerate(places, start=1):
        name = p.get("name") or p.get("property_name") or "Unnamed Landmark"
        rating = p.get("rating", 5.0)
        try:
            rating_num = float(rating)
        except (ValueError, TypeError):
            rating_num = 5.0
        rating_str = f"Rating: {rating_num:.1f}/5 ⭐"

        raw_cats = p.get("categories") or []
        clean_cats = [
            c.split(".")[-1].replace("_", " ").title()
            for c in raw_cats[:3]
            if c not in ("tourism", "building", "no_fee", "no_fee.no", "no_fee.yes")
        ]
        cat_str = f" [{', '.join(clean_cats)}]" if clean_cats else ""
        addr = p.get("address", "")
        first_addr = addr.split(",")[0].strip() if addr else ""
        addr_short = f" — {first_addr}" if first_addr and first_addr.lower() != name.lower() else ""
        lines.append(f"  {idx:2d}. {name} — {rating_str}{cat_str}{addr_short}")
    lines.append(f"{'=' * 80}")
    return "\n".join(lines)


def _normalize_apify_attractions(raw_data: Any, city: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Normalize raw tourist attractions returned by Apify MCP Actor into standard places schema, resolving datasets where needed."""
    import re
    from app.agents.accommodation.normalizer import extract_raw_json
    parsed = extract_raw_json(raw_data)
    items = []

    # If Apify MCP returned an actor run summary with dataset ID, fetch the dataset items
    dataset_id = None
    run_id = None
    status = None
    if isinstance(parsed, dict):
        dataset_id = (
            parsed.get("storages", {}).get("datasets", {}).get("default", {}).get("id")
            or parsed.get("defaultDatasetId")
        )
        run_id = parsed.get("runId") or parsed.get("id")
        status = parsed.get("status")
        if not dataset_id and "datasetId" in str(parsed):
            m = re.search(r"datasetId=([a-zA-Z0-9]+)", str(parsed))
            if m:
                dataset_id = m.group(1)
        if not run_id and "runId" in str(parsed):
            m2 = re.search(r"runId=([a-zA-Z0-9]+)", str(parsed))
            if m2:
                run_id = m2.group(1)

    if dataset_id or run_id:
        try:
            import httpx
            from app.core.config import settings
            headers = {}
            if settings.clean_apify_token:
                headers["Authorization"] = f"Bearer {settings.clean_apify_token}"

            # If actor run is currently in progress, wait for it to complete (up to 60s)
            if status == "RUNNING" and run_id:
                logger.info(f"Apify Actor run '{run_id}' is executing. Waiting for dataset completion...")
                try:
                    run_resp = httpx.get(
                        f"https://api.apify.com/v2/actor-runs/{run_id}?waitForFinish=60",
                        headers=headers,
                        timeout=65.0,
                    )
                    if run_resp.status_code == 200:
                        run_data = run_resp.json().get("data", {})
                        dataset_id = run_data.get("defaultDatasetId") or dataset_id
                except Exception as wexc:
                    logger.warning(f"Wait for Apify actor run failed: {wexc}")

            if dataset_id:
                logger.info(f"Fetching {city} items from Apify dataset '{dataset_id}'...")
                res = httpx.get(
                    f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                    headers=headers,
                    timeout=20.0,
                )
                if res.status_code == 200:
                    ds_items = res.json()
                    if isinstance(ds_items, list) and ds_items:
                        # Ignore single placeholder messages like 'No places could be extracted' or 'No cities found'
                        if not (
                            len(ds_items) == 1
                            and "message" in ds_items[0]
                            and any(kw in str(ds_items[0]["message"]).lower() for kw in ("no places", "no cities", "not found"))
                        ):
                            items = ds_items
        except Exception as exc:
            logger.warning(f"Failed to fetch Apify dataset {dataset_id}: {exc}")

    if not items:
        if isinstance(parsed, list):
            items = parsed
        elif isinstance(parsed, dict):
            items = parsed.get("attractions") or parsed.get("places") or parsed.get("results") or parsed.get("data") or []

    normalized = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("placeName") or item.get("title") or item.get("name")
        if not name or len(str(name).strip()) < 2:
            continue
        clean_name = str(name).strip()
        name_key = clean_name.lower()
        if name_key in seen:
            continue
        seen.add(name_key)

        rating_val = item.get("rating") or item.get("stars") or 5.0
        try:
            rating_num = float(rating_val)
        except (ValueError, TypeError):
            rating_num = 5.0

        raw_categories = item.get("categories") or ([item.get("category")] if item.get("category") else ["tourist attractions"])
        if isinstance(raw_categories, str):
            raw_categories = [raw_categories]

        normalized.append({
            "name": clean_name,
            "rating": rating_num,
            "rating_text": f"{rating_num:.1f}/5 ⭐",
            "star_rating": int(round(rating_num)),
            "is_famous": True,
            "fame_tier": f"Famous Landmark · Rated {rating_num:.1f}/5 ⭐",
            "address": item.get("address") or item.get("formattedAddress") or f"{clean_name}, {city}",
            "city": city,
            "latitude": item.get("latitude") or item.get("lat"),
            "longitude": item.get("longitude") or item.get("lng") or item.get("lon"),
            "categories": raw_categories,
            "data_source": "apify_mcp",
        })

    normalized.sort(key=lambda x: x["rating"], reverse=True)
    return normalized[:limit] if limit is not None else normalized


@tool
def search_places(city: str, category: str = "tourism.sights", limit: Optional[int] = None) -> ToolResult:
    """Search all famous tourist attractions, heritage monuments, iconic palaces, forts, museums, and lakes in a destination city. Primarily queries Apify MCP Server with automatic Geoapify fallback."""
    logger.info(f"Places Tool invoked for city='{city}', category='{category}', limit={limit}")
    if not city or not str(city).strip():
        return ToolResult(success=False, error="City name cannot be empty.", data=[])

    cache_key = f"{str(city).strip().lower()}_{category}_{limit}"
    cached = places_cache.get(cache_key)
    if cached is not None:
        logger.info(f"[PlacesTool] Cache HIT for key='{cache_key}' (sub-millisecond return)")
        return cached

    # 1. PRIMARY PROVIDER: Apify MCP Server (happitap/city-tourism-attractions-finder)
    from app.core.config import settings
    if not settings.clean_apify_token:
        logger.info(
            "ℹ️  [Apify MCP Notice] 'APIFY_TOKEN' is not configured in .env. "
            "Apify MCP server requires an Apify API token (HTTP 401). "
            "Seamlessly activating Fallback: Geoapify Places API."
        )
    else:
        # Normalize city names for the Apify Happitap Actor (it indexes 'Bangalore' instead of 'Bengaluru')
        apify_city_map = {
            "bengaluru": "Bangalore",
            "calcutta": "Kolkata",
            "bombay": "Mumbai",
            "madras": "Chennai",
            "cochin": "Kochi",
            "trivandrum": "Thiruvananthapuram",
            "benaras": "Varanasi",
            "banaras": "Varanasi",
        }
        clean_city = str(city).strip()
        apify_city = apify_city_map.get(clean_city.lower(), clean_city)

        logger.info(f"[Primary Provider] Querying Apify MCP Server (happitap/city-tourism-attractions-finder) for '{apify_city}' famous attractions...")
        try:
            from app.mcp.remote import remote_mcp_manager
            mcp_res = remote_mcp_manager.execute_tool(
                agent_name="destination_agent",
                tool_name="apify_happitap_city_tourism_attractions_finder",
                arguments={
                    "searchMode": "CITY_NAME",
                    "cityName": apify_city,
                    "categories": ["tourist attractions"],
                    "maxResultsPerCategory": limit or 30,
                    "language": "en",
                },
            )
            if mcp_res.get("success") and mcp_res.get("data"):
                normalized_apify = _normalize_apify_attractions(mcp_res["data"], city=city, limit=limit)
                if normalized_apify:
                    logger.info(f"Successfully retrieved {len(normalized_apify)} famous attractions from Apify MCP server.")
                    cli_table = format_places_cli_table(
                        normalized_apify,
                        city=city,
                        provider="Apify MCP Server (happitap/city-tourism-attractions-finder) [Primary]",
                    )
                    logger.info(f"\n{cli_table}")
                    res = ToolResult(
                        success=True,
                        data=normalized_apify,
                        metadata={
                            "provider": "Apify MCP Server (happitap/city-tourism-attractions-finder)",
                            "mcp_server": "apify",
                            "mcp_tool": "happitap/city-tourism-attractions-finder",
                            "is_primary": True,
                        },
                    )
                    places_cache.set(cache_key, res)
                    return res
                else:
                    logger.warning("Apify MCP returned no parsed tourist attractions. Activating Fallback: Geoapify Places API.")
            else:
                err_notice = mcp_res.get("error", "No data returned")
                logger.warning(f"Apify MCP Server (Primary) returned unsuccessful ({err_notice}). Activating Fallback: Geoapify Places API.")
        except Exception as exc:
            logger.warning(f"Apify MCP Server (Primary) call skipped or failed ({exc}). Activating Fallback: Geoapify Places API.")

    # 2. RESILIENT FALLBACK: Geoapify Places Service with verified fame ranking and 5-star rating
    logger.info(f"[Fallback Provider] Executing Geoapify Places API for '{city}' famous landmarks...")
    data = _places_service.search_places(
        city=city,
        category=category,
        limit=limit,
    )

    cli_table = format_places_cli_table(
        data,
        city=city,
        provider="Geoapify Places API (Fallback from Apify MCP)",
    )
    logger.info(f"\n{cli_table}")

    fallback_res = ToolResult(
        success=True,
        data=data,
        metadata={
            "provider": "Geoapify Places API (Fallback from Apify MCP)",
            "primary_provider": "Apify MCP Server (happitap/city-tourism-attractions-finder)",
            "fallback_used": True,
            "mcp_server": None,
            "source": "geoapify_places",
        },
    )
    if data:
        places_cache.set(cache_key, fallback_res)
    return fallback_res


class PlacesTool:
    def search_places(self, city: str, category: str = "tourism.sights", limit: Optional[int] = None) -> ToolResult:
        args = {"city": city, "category": category}
        if limit is not None:
            args["limit"] = limit
        return search_places.invoke(args)
