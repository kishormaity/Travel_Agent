import os
import sys
import subprocess
import time
import threading
from typing import Any, Dict, List, Optional
import requests
from loguru import logger
from app.mcp.remote import remote_mcp_manager
from app.schemas.agents import FlightAgentOutput
from app.schemas.flight import NormalizedFlightOffer
from app.agents.flight.normalizer import (
    extract_raw_json,
    normalize_octotrip_flight,
    normalize_fli_flight,
    rank_flight_offers,
)
from app.core.observability import (
    log_specialist_task_start,
    log_specialist_task_end,
)
from app.services.request_normalizer import resolve_airport_code


def _ensure_fli_running() -> bool:
    """Auto-start the local Fli Google Flights MCP server if not already reachable."""
    health_url = os.getenv("FLI_HEALTH_URL", "http://127.0.0.1:8001/health")
    try:
        if requests.get(health_url, timeout=1).status_code == 200:
            return True
    except Exception:
        pass

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        subprocess.Popen(
            [sys.executable, "-m", "app.mcp.servers.fli_server"],
            cwd=base_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            try:
                if requests.get(health_url, timeout=1).status_code == 200:
                    logger.info("Auto-started Fli Google Flights MCP server on port 8001.")
                    return True
            except Exception:
                time.sleep(0.2)
    except Exception as e:
        logger.warning(f"Could not auto-start Fli server: {e}")
    return False


class FlightAgent:
    """
    Specialized agent responsible for searching, normalizing, and ranking flight options.
    Implements multi-provider strategy: prefers Fli (Google Flights MCP) when healthy;
    falls back to OctoTrip when Fli is offline or unavailable.
    Includes in-memory search deduplication caching, bounded retries, and airport code normalization.
    """

    _flight_cache: Dict[str, tuple[float, FlightAgentOutput]] = {}
    _cache_lock = threading.Lock()

    @classmethod
    def clear_cache(cls) -> None:
        """Clears the in-memory flight search cache."""
        with cls._cache_lock:
            cls._flight_cache.clear()

    def __init__(self):
        self.agent_name = "flight_agent"
        self.mcp_provider = "flight_octotrip"

    def _map_cabin_class(self, trip_class: Optional[str]) -> str:
        """Map generic cabin class string to Fli's expected cabin enum."""
        if not trip_class:
            return "ECONOMY"
        tc = str(trip_class).strip().upper()
        if tc in ("Y", "ECONOMY", "M"):
            return "ECONOMY"
        if tc in ("W", "PREMIUM", "PREMIUM_ECONOMY", "PREMIUM-ECONOMY"):
            return "PREMIUM_ECONOMY"
        if tc in ("C", "J", "BUSINESS"):
            return "BUSINESS"
        if tc in ("F", "FIRST"):
            return "FIRST"
        return "ECONOMY"

    def _map_max_stops(self, max_stops: Any) -> str:
        """Map max stops preference to Fli's expected max stops enum."""
        if max_stops is None:
            return "ANY"
        ms = str(max_stops).strip().upper()
        if ms in ("0", "DIRECT", "NONSTOP", "NON_STOP"):
            return "NON_STOP"
        if ms in ("1", "ONE_STOP"):
            return "ONE_STOP"
        if ms in ("2", "2+", "TWO_PLUS_STOPS"):
            return "TWO_PLUS_STOPS"
        return "ANY"

    def execute(
        self,
        departure_iata: Optional[str] = None,
        arrival_iata: Optional[str] = None,
        flight_date: Optional[str] = None,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        trip_class: str = "Y",
        currency: Optional[str] = None,
        **kwargs,
    ) -> FlightAgentOutput:
        start_time = time.time()
        task_id = kwargs.get("_task_id", "flight_search")
        bypass_cache = kwargs.get("bypass_cache", False)

        # Support alias names from planners/schemas
        raw_origin = departure_iata or kwargs.get("origin")
        raw_destination = arrival_iata or kwargs.get("destination")
        dep_date = flight_date or kwargs.get("departure_date") or kwargs.get("start_date")
        ret_date = return_date or kwargs.get("return_date") or kwargs.get("end_date")
        preferred_currency = currency or kwargs.get("preferred_currency") or "INR"

        # ---------------------------------------------------------------------
        # Airport Code Normalization and Strict Validation
        # Udaipur must ALWAYS resolve to UDR; reject/correct invalid codes like UDI
        # ---------------------------------------------------------------------
        origin = resolve_airport_code(str(raw_origin), context_hint=str(raw_origin)) if raw_origin else None
        destination = resolve_airport_code(str(raw_destination), context_hint=str(raw_destination)) if raw_destination else None

        if not origin and raw_origin:
            origin = str(raw_origin).strip().upper()
        if not destination and raw_destination:
            destination = str(raw_destination).strip().upper()

        if destination == "UDI":
            logger.warning(f"[{self.agent_name}] Intercepted invalid airport code 'UDI'. Corrected to canonical 'UDR' (Udaipur).")
            destination = "UDR"
        if origin == "UDI":
            logger.warning(f"[{self.agent_name}] Intercepted invalid airport code 'UDI'. Corrected to canonical 'UDR' (Udaipur).")
            origin = "UDR"

        if not origin or not destination:
            return FlightAgentOutput(
                success=False,
                error="Both origin/departure and destination/arrival airport codes or city names are required. At least one search filter must specify valid route endpoints.",
                summary=f"Missing origin or destination for flight search (origin={origin}, destination={destination}).",
                flights=[],
                data={"count": 0, "flights": [], "ranked": {}, "provider": "none"},
                execution_time_ms=(time.time() - start_time) * 1000.0,
            )

        if not dep_date:
            return FlightAgentOutput(
                success=False,
                error="Departure flight date is required for flight search.",
                summary="Missing departure flight date for flight search.",
                flights=[],
                data={"count": 0, "flights": [], "ranked": {}, "provider": "none"},
                execution_time_ms=(time.time() - start_time) * 1000.0,
            )

        mapped_cabin: str = self._map_cabin_class(kwargs.get("cabin_class") or trip_class)
        mapped_stops: str = self._map_max_stops(kwargs.get("max_stops", "ANY"))

        # ---------------------------------------------------------------------
        # 0. Check In-Memory Deduplication Cache
        # ---------------------------------------------------------------------
        cache_key = f"{origin}:{destination}:{dep_date}:{ret_date}:{adults}:{children}:{infants}:{mapped_cabin}:{mapped_stops}:{preferred_currency}"
        if not bypass_cache:
            with self._cache_lock:
                if cache_key in self._flight_cache:
                    cached_time, cached_out = self._flight_cache[cache_key]
                    if time.time() - cached_time < 1800.0:  # 30-minute valid TTL
                        is_valid_cache = True
                        if mapped_stops == "NON_STOP":
                            if any(f.get("stops", 0) > 0 or f.get("is_direct") is False for f in (cached_out.flights or [])):
                                is_valid_cache = False
                        if is_valid_cache:
                            logger.info(
                                f"[{self.agent_name}] Cache HIT for flight search {cache_key} "
                                f"(age: {time.time() - cached_time:.1f}s, offers: {len(cached_out.flights)})"
                            )
                            return cached_out.model_copy(update={"execution_time_ms": (time.time() - start_time) * 1000.0})
                        else:
                            del self._flight_cache[cache_key]

        _ensure_fli_running()
        remote_mcp_manager.ensure_initialized()

        all_normalized_offers: List[NormalizedFlightOffer] = []
        raw_response: Any = None
        chosen_provider: str = "none"
        provider_display_name: str = "None"
        fli_error: Optional[str] = None
        ot_error: Optional[str] = None
        not_found_advice: Optional[str] = None

        # ---------------------------------------------------------------------
        # 1. Primary Flight Provider: Fli (Google Flights MCP)
        # ---------------------------------------------------------------------
        fli_tool = next(
            (name for name in remote_mcp_manager._tools_cache if name.startswith("fli_search_flights") or name == "fli_search_flights" or name == "search_flights"),
            None,
        )

        if not fli_tool:
            try:
                if _ensure_fli_running():
                    remote_mcp_manager._initialized = False
                    remote_mcp_manager.ensure_initialized()
                    fli_tool = next(
                        (name for name in remote_mcp_manager._tools_cache if name.startswith("fli_search_flights") or name == "fli_search_flights" or name == "search_flights"),
                        None,
                    )
            except Exception as e:
                logger.warning(f"[{self.agent_name}] Could not auto-ensure Fli server: {e}")

        if fli_tool:
            logger.info(
                f"[{self.agent_name}] Initiating Fli flight search: origin={origin}, dest={destination}, "
                f"dep_date={dep_date}, return_date={ret_date}, adults={adults}, currency={preferred_currency}"
            )
            fli_args: Dict[str, Any] = {
                "origin": origin,
                "destination": destination,
                "departure_date": dep_date,
                "cabin_class": self._map_cabin_class(kwargs.get("cabin_class") or trip_class),
                "max_stops": self._map_max_stops(kwargs.get("max_stops", "ANY")),
                "passengers": max(1, adults),
                "children": max(0, children),
                "infants_in_seat": max(0, infants),
                "currency": preferred_currency,
            }
            if ret_date:
                fli_args["return_date"] = ret_date

            t0 = log_specialist_task_start(
                task_id=task_id,
                specialist_name=self.agent_name,
                selected_mcp_server="fli",
                selected_tool=fli_tool,
                arguments=fli_args,
            )

            try:
                fli_res = remote_mcp_manager.execute_tool(
                    agent_name=self.agent_name,
                    tool_name=fli_tool,
                    arguments=fli_args,
                )
                logger.info(f"[{self.agent_name}] FULL FLI MCP RAW RESULT: success={fli_res.get('success')}, error={fli_res.get('error')}")

                if fli_res.get("success"):
                    raw_data = fli_res.get("data")
                    parsed = extract_raw_json(raw_data)
                    flights_list = []
                    if isinstance(parsed, dict) and "flights" in parsed:
                        flights_list = parsed["flights"]
                    elif isinstance(parsed, list):
                        flights_list = parsed

                    logger.info(f"[{self.agent_name}] Fli returned {len(flights_list)} raw flight offers.")

                    mapped_cabin = fli_args.get("cabin_class", "ECONOMY")
                    mapped_stops = fli_args.get("max_stops", "ANY")

                    def _filter_and_normalize(items: list) -> List[NormalizedFlightOffer]:
                        res_list = []
                        for item in items:
                            try:
                                offer = normalize_fli_flight(
                                    item=item,
                                    origin_hint=origin,
                                    dest_hint=destination,
                                    preferred_currency=preferred_currency,
                                    adults=adults,
                                    children=children,
                                    infants=infants,
                                    is_round_trip_requested=bool(ret_date),
                                )
                                # 1. Strict Price Validation: Discard unpriced or zero-fare offers
                                if not offer.price or float(offer.price) <= 0:
                                    continue

                                # 2. Strict Stops Validation: Never inject connecting flights when Non-Stop was requested
                                if mapped_stops == "NON_STOP" and (not offer.is_direct or offer.stops > 0):
                                    continue
                                if mapped_stops == "ONE_STOP" and offer.stops > 1:
                                    continue

                                # 3. Strict Cabin Validation: Never substitute unrequested classes
                                offer_fare = (offer.fare_type or "").upper()
                                if mapped_cabin == "BUSINESS" and "BUSINESS" not in offer_fare:
                                    continue
                                if mapped_cabin == "FIRST" and "FIRST" not in offer_fare:
                                    continue
                                if mapped_cabin == "PREMIUM_ECONOMY" and "PREMIUM" not in offer_fare:
                                    continue

                                res_list.append(offer)
                            except Exception as ne:
                                logger.warning(f"[{self.agent_name}] Error normalizing Fli flight item: {ne}")
                        return res_list

                    all_normalized_offers = _filter_and_normalize(flights_list)

                    # If 0 offers and children/infants were specified, Google Flights server doesn't inline
                    # rows due to client-side pricing. Query adult base schedule KEEPING exact same cabin and stops.
                    if not all_normalized_offers and (children > 0 or infants > 0):
                        f_adult = dict(fli_args)
                        f_adult["passengers"] = max(1, adults)
                        f_adult["children"] = 0
                        f_adult["infants_in_seat"] = 0
                        try:
                            logger.info(f"[{self.agent_name}] Querying adult schedule for {mapped_cabin} / {mapped_stops} to check true availability...")
                            adult_res = remote_mcp_manager.execute_tool(
                                agent_name=self.agent_name,
                                tool_name=fli_tool,
                                arguments=f_adult,
                            )
                            if adult_res.get("success"):
                                adult_raw = extract_raw_json(adult_res.get("data"))
                                adult_list = adult_raw.get("flights", []) if isinstance(adult_raw, dict) else (adult_raw if isinstance(adult_raw, list) else [])
                                all_normalized_offers = _filter_and_normalize(adult_list)
                                if all_normalized_offers:
                                    parsed = adult_raw
                        except Exception as e_ad:
                            logger.warning(f"[{self.agent_name}] Adult schedule check failed: {e_ad}")

                    # If still 0 offers, DO NOT FAKE OR SUBSTITUTE OTHER CABINS/STOPS!
                    # Construct an honest, informative explanation advising the user.
                    if not all_normalized_offers:
                        if mapped_cabin in ("BUSINESS", "FIRST") and mapped_stops == "NON_STOP":
                            not_found_advice = (
                                f"No direct non-stop {mapped_cabin.title()} Class flights operate on the {origin} ➔ {destination} route. "
                                f"Direct flights on this route are operated exclusively in Economy class (e.g. IndiGo, Akasa Air, Air India Express). "
                                f"Please check Economy class for direct non-stop flights, or select 'Any Stops' to search for connecting {mapped_cabin.title()} Class itineraries."
                            )
                        elif mapped_cabin in ("BUSINESS", "FIRST"):
                            not_found_advice = (
                                f"No {mapped_cabin.title()} Class flights were found for {origin} ➔ {destination} on {dep_date}. "
                                f"Please check Economy class for available flights."
                            )
                        elif mapped_stops == "NON_STOP":
                            not_found_advice = (
                                f"No direct non-stop flights were found for {origin} ➔ {destination} on {dep_date}. "
                                f"Please search with 'Any Stops' to view connecting flight options."
                            )
                        else:
                            not_found_advice = (
                                f"No flights found matching your exact search filters for {origin} ➔ {destination} on {dep_date}. "
                                f"Please check alternative dates or Economy class."
                            )
                        fli_error = None
                    else:
                        not_found_advice = None

                    if all_normalized_offers:
                        chosen_provider = "fli"
                        provider_display_name = "Fli (Google Flights)"
                        raw_response = parsed
                        log_specialist_task_end(
                            task_id=task_id,
                            specialist_name=self.agent_name,
                            selected_mcp_server="fli",
                            selected_tool=fli_tool,
                            start_time=t0,
                            status="COMPLETED",
                            raw_response={
                                "count": len(all_normalized_offers),
                                "flights": [
                                    {
                                        "airline": o.airline,
                                        "flight_number": o.flight_number,
                                        "departure": f"{o.departure_date} {o.departure_time}",
                                        "arrival": f"{o.arrival_date} {o.arrival_time}",
                                        "duration": o.duration_formatted,
                                        "price": o.price,
                                        "currency": o.currency,
                                        "booking_url": o.booking_url,
                                    }
                                    for o in all_normalized_offers
                                ],
                            },
                        )
                    else:
                        log_specialist_task_end(
                            task_id=task_id,
                            specialist_name=self.agent_name,
                            selected_mcp_server="fli",
                            selected_tool=fli_tool,
                            start_time=t0,
                            status="COMPLETED",
                            raw_response={"status": "NOT_FOUND", "notice": not_found_advice},
                        )
                else:
                    fli_error = fli_res.get("error") or "Fli tool returned failure"
                    log_specialist_task_end(
                        task_id=task_id,
                        specialist_name=self.agent_name,
                        selected_mcp_server="fli",
                        selected_tool=fli_tool,
                        start_time=t0,
                        status="FAILED",
                        raw_response=fli_res,
                    )
            except Exception as e:
                fli_error = str(e)
                logger.warning(f"[{self.agent_name}] Fli invocation exception: {e}")
                log_specialist_task_end(
                    task_id=task_id,
                    specialist_name=self.agent_name,
                    selected_mcp_server="fli",
                    selected_tool=fli_tool,
                    start_time=t0,
                    status="FAILED",
                    exception=e,
                )

        # ---------------------------------------------------------------------
        # 2. Fallback Flight Provider: OctoTrip (only if Fli had an error/outage)
        # ---------------------------------------------------------------------
        if not all_normalized_offers and fli_error:
            if fli_error:
                logger.warning(f"[{self.agent_name}] Fli MCP unavailable or failed ({fli_error}). Falling back to OctoTrip...")

            octotrip_tool = next(
                (name for name in remote_mcp_manager._tools_cache if "octotrip" in name.lower()),
                "flight_octotrip_search",
            )

            ot_args: Dict[str, Any] = {
                "origin": origin,
                "destination": destination,
                "departure_date": dep_date,
                "adults": max(1, min(adults, 9)),
                "children": max(0, min(children, 9)),
                "infants": max(0, min(infants, 9)),
                "trip_class": trip_class,
                "currency": preferred_currency,
            }
            if ret_date:
                ot_args["return_date"] = ret_date

            t0_ot = log_specialist_task_start(
                task_id=task_id,
                specialist_name=self.agent_name,
                selected_mcp_server=self.mcp_provider,
                selected_tool=octotrip_tool,
                arguments=ot_args,
            )

            max_retries = 0
            ot_res: Optional[Dict[str, Any]] = None

            for attempt in range(max_retries + 1):
                try:
                    ot_res = remote_mcp_manager.execute_tool(
                        agent_name=self.agent_name,
                        tool_name=octotrip_tool,
                        arguments=ot_args,
                    )
                    if ot_res.get("success") and ot_res.get("data"):
                        break
                except Exception as e:
                    logger.warning(f"[{self.agent_name}] OctoTrip attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    time.sleep(1.0 * (attempt + 1))

            try:
                if ot_res and ot_res.get("success") and ot_res.get("data"):
                    raw_data = ot_res.get("data")
                    parsed = extract_raw_json(raw_data)
                    ot_results = []
                    if isinstance(parsed, dict) and "flights" in parsed:
                        ot_results = parsed["flights"]
                    elif isinstance(parsed, list):
                        ot_results = parsed

                    for item in ot_results:
                        offer = normalize_octotrip_flight(
                            item=item,
                            origin_hint=origin,
                            dest_hint=destination,
                            adults=adults,
                            children=children,
                            infants=infants,
                            currency=preferred_currency,
                        )
                        all_normalized_offers.append(offer)

                    if all_normalized_offers:
                        chosen_provider = "flight_octotrip"
                        provider_display_name = "OctoTrip"
                        raw_response = parsed
                        log_specialist_task_end(
                            task_id=task_id,
                            specialist_name=self.agent_name,
                            selected_mcp_server=self.mcp_provider,
                            selected_tool=octotrip_tool,
                            start_time=t0_ot,
                            status="COMPLETED",
                            raw_response={"count": len(all_normalized_offers)},
                        )
                    else:
                        ot_error = "OctoTrip returned 0 offers"
                else:
                    ot_error = (ot_res.get("error") if ot_res else None) or "No data returned from OctoTrip MCP"
                    log_specialist_task_end(
                        task_id=task_id,
                        specialist_name=self.agent_name,
                        selected_mcp_server=self.mcp_provider,
                        selected_tool=octotrip_tool,
                        start_time=t0_ot,
                        status="FAILED",
                        raw_response=ot_res,
                    )
            except Exception as e:
                ot_error = str(e)
                logger.error(f"[{self.agent_name}] OctoTrip processing exception: {e}")
                log_specialist_task_end(
                    task_id=task_id,
                    specialist_name=self.agent_name,
                    selected_mcp_server=self.mcp_provider,
                    selected_tool=octotrip_tool,
                    start_time=t0_ot,
                    status="FAILED",
                    exception=e,
                )

        # ---------------------------------------------------------------------
        # 3. Provider Outage / Clean Not-Found Handling
        # ---------------------------------------------------------------------
        if not all_normalized_offers:
            if fli_error and ot_error:
                combined_err = f"All flight providers failed. Fli: {fli_error}; OctoTrip: {ot_error}"
                logger.error(f"[{self.agent_name}] {combined_err}")
                return FlightAgentOutput(
                    success=False,
                    error=combined_err,
                    summary=f"Unable to retrieve flights between {origin} and {destination}. All providers failed ({combined_err}).",
                    flights=[],
                    data={"count": 0, "flights": [], "ranked": {}, "provider": "none", "provider_display_name": "None"},
                    execution_time_ms=(time.time() - start_time) * 1000.0,
                )

            clean_summary = not_found_advice or f"No flights found matching the requested filters for {origin} ➔ {destination} on {dep_date}."
            logger.info(f"[{self.agent_name}] Clean search completed: 0 matching flights found. Notice: {clean_summary}")
            return FlightAgentOutput(
                success=True,
                error=None,
                summary=clean_summary,
                flights=[],
                data={
                    "count": 0,
                    "flights": [],
                    "status": "NOT_FOUND",
                    "notice": clean_summary,
                    "origin": origin,
                    "destination": destination,
                    "departure_date": dep_date,
                    "cabin_class": mapped_cabin,
                    "max_stops": mapped_stops,
                    "provider": "fli" if fli_tool else "none",
                    "provider_display_name": "Fli (Google Flights)" if fli_tool else "None",
                },
                execution_time_ms=(time.time() - start_time) * 1000.0,
            )

        # ---------------------------------------------------------------------
        # 4. Ranking and Output Synthesis
        # ---------------------------------------------------------------------
        ranked = rank_flight_offers(all_normalized_offers)
        ranked_matching = [o for o in ranked["best_value"] if o.route_match]
        ranked_non_matching = [o for o in ranked["best_value"] if not o.route_match]
        ordered_offers = ranked_matching + ranked_non_matching if ranked_matching else ranked["best_value"]
        flight_dicts = [offer.model_dump() for offer in ordered_offers]

        elapsed_ms = (time.time() - start_time) * 1000.0
        best_opt = ordered_offers[0]
        cheapest_opt = ranked["cheapest"][0] if ranked["cheapest"] else best_opt
        fastest_opt = ranked["fastest"][0] if ranked["fastest"] else best_opt

        is_rt = any(o.is_round_trip for o in all_normalized_offers)
        trip_type_str = "round-trip" if is_rt else "one-way"
        price_suffix = "total round-trip" if is_rt else "one-way"

        duration_details = (
            f"{best_opt.duration_formatted} total (outbound: {best_opt.outbound_duration_formatted or 'N/A'}, "
            f"return: {best_opt.inbound_duration_formatted or 'N/A'})"
            if is_rt and best_opt.outbound_duration_formatted
            else best_opt.duration_formatted
        )

        route_validation_note = ""
        if any(not o.route_match for o in all_normalized_offers):
            route_validation_note = " Note: Some results had airport/route mismatches and have been flagged."

        best_airline_str = best_opt.outbound_airline or best_opt.airline
        if is_rt and best_opt.inbound_airline and best_opt.inbound_airline != best_opt.outbound_airline:
            best_airline_str = f"Outbound: {best_opt.outbound_airline}, Return: {best_opt.inbound_airline}"

        category_notes: List[str] = []
        if best_opt.provider_flight_id == cheapest_opt.provider_flight_id == fastest_opt.provider_flight_id:
            category_notes.append(
                f"Option {best_opt.flight_number or 'opt'} ({best_airline_str}) is simultaneously ranked as Best Value, Cheapest, and Fastest "
                f"because it combines the lowest verified fare of {best_opt.price:.2f} {best_opt.currency} "
                f"with the shortest overall journey duration ({duration_details}) and 0 layover stops."
            )
        elif best_opt.provider_flight_id == cheapest_opt.provider_flight_id:
            category_notes.append(
                f"Option {best_opt.flight_number or 'opt'} ({best_airline_str}) is both Best Value and Cheapest due to offering the lowest verified fare ({best_opt.price:.2f} {best_opt.currency}) with optimal travel time."
            )
        elif best_opt.provider_flight_id == fastest_opt.provider_flight_id:
            category_notes.append(
                f"Option {best_opt.flight_number or 'opt'} ({best_airline_str}) is both Best Value and Fastest due to offering the shortest journey duration."
            )
        category_note_str = f" {' '.join(category_notes)}" if category_notes else ""

        summary = (
            f"Found {len(all_normalized_offers)} {trip_type_str} flight option(s) between "
            f"{origin} and {destination} via {provider_display_name}. "
            f"Best Value: {best_airline_str} ({best_opt.flight_number or 'N/A'}) at {best_opt.price:.2f} {best_opt.currency} {price_suffix} ({duration_details}); "
            f"Cheapest: {cheapest_opt.outbound_airline or cheapest_opt.airline} at {cheapest_opt.price:.2f} {cheapest_opt.currency} {price_suffix}; "
            f"Fastest: {fastest_opt.outbound_airline or fastest_opt.airline} ({fastest_opt.duration_formatted} total).{category_note_str}{route_validation_note}"
        )

        ranked_highlights = {
            "best_value": best_opt.model_dump(),
            "cheapest": cheapest_opt.model_dump(),
            "fastest": fastest_opt.model_dump(),
        }

        output_obj = FlightAgentOutput(
            success=True,
            error=None,
            summary=summary,
            flights=flight_dicts,
            data={
                "count": len(all_normalized_offers),
                "flights": flight_dicts,
                "ranked_highlights": ranked_highlights,
                "category_overlap_explanation": " ".join(category_notes) if category_notes else None,
                "ranked": {
                    "best_value": [f.model_dump() for f in ranked["best_value"]],
                    "cheapest": [f.model_dump() for f in ranked["cheapest"]],
                    "fastest": [f.model_dump() for f in ranked["fastest"]],
                    "fewest_stops": [f.model_dump() for f in ranked["fewest_stops"]],
                },
                "provider": chosen_provider,
                "provider_display_name": provider_display_name,
                "raw_response": raw_response,
            },
            execution_time_ms=elapsed_ms,
        )

        with self._cache_lock:
            self._flight_cache[cache_key] = (time.time(), output_obj)

        return output_obj

    def execute_separate_roundtrip_legs(
        self,
        departure_iata: str,
        arrival_iata: str,
        flight_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
        trip_class: str = "Y",
        currency: str = "INR",
        bypass_cache: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Executes individual one-way flight searches for Outbound (Going) and Return (Inbound) legs.
        Identifies the best cheapest for Going and Returning, and returns full lists of both.
        """
        # 1. Going leg
        outbound_res = self.execute(
            departure_iata=departure_iata,
            arrival_iata=arrival_iata,
            flight_date=flight_date,
            return_date=None,
            adults=adults,
            children=children,
            infants=infants,
            trip_class=trip_class,
            currency=currency,
            bypass_cache=bypass_cache,
            **kwargs,
        )

        outbound_offers = []
        if outbound_res.success and outbound_res.flights:
            for f in outbound_res.flights:
                f_dict = f if isinstance(f, dict) else f.model_dump()
                f_dict["direction"] = "outbound"
                f_dict["journey_label"] = f"Going ({departure_iata} ➔ {arrival_iata})"
                f_dict["is_round_trip"] = bool(return_date)
                outbound_offers.append(f_dict)
            outbound_offers.sort(key=lambda x: float(x.get("price") or 0))
            if outbound_offers:
                min_p = float(outbound_offers[0].get("price") or 0)
                for f in outbound_offers:
                    f["is_lowest_price"] = (float(f.get("price") or 0) == min_p)

        # 2. Returning leg
        return_offers = []
        if return_date:
            return_res = self.execute(
                departure_iata=arrival_iata,
                arrival_iata=departure_iata,
                flight_date=return_date,
                return_date=None,
                adults=adults,
                children=children,
                infants=infants,
                trip_class=trip_class,
                currency=currency,
                bypass_cache=bypass_cache,
                **kwargs,
            )
            if return_res.success and return_res.flights:
                for f in return_res.flights:
                    f_dict = f if isinstance(f, dict) else f.model_dump()
                    f_dict["direction"] = "return"
                    f_dict["journey_label"] = f"Returning ({arrival_iata} ➔ {departure_iata})"
                    f_dict["is_round_trip"] = True
                    return_offers.append(f_dict)
                return_offers.sort(key=lambda x: float(x.get("price") or 0))
                if return_offers:
                    min_p = float(return_offers[0].get("price") or 0)
                    for f in return_offers:
                        f["is_lowest_price"] = (float(f.get("price") or 0) == min_p)

        all_flights = outbound_offers + return_offers
        provider = (outbound_res.data.get("provider") if outbound_res.data else None) or "fli"
        
        notices = []
        if not outbound_offers and outbound_res.summary:
            notices.append(f"Outbound: {outbound_res.summary}")
        if return_date and not return_offers and return_res and return_res.summary:
            notices.append(f"Return: {return_res.summary}")
        combined_notice = " ".join(notices) if notices else None

        return {
            "success": True,
            "outbound_flights": outbound_offers,
            "return_flights": return_offers,
            "all_flights": all_flights,
            "cheapest_outbound": outbound_offers[0] if outbound_offers else None,
            "cheapest_return": return_offers[0] if return_offers else None,
            "provider": provider,
            "notice": combined_notice,
            "status": "NOT_FOUND" if not all_flights else "FOUND",
        }

    def search_dates(
        self,
        origin: str,
        destination: str,
        start_date: str,
        end_date: str,
        trip_duration: int = 3,
        is_round_trip: bool = False,
        currency: str = "INR",
        **kwargs,
    ) -> Dict[str, Any]:
        """Query flight date fare calendar via Fli MCP server."""
        remote_mcp_manager.ensure_initialized()
        fli_tool = next(
            (name for name in remote_mcp_manager._tools_cache if name.startswith("fli_search_dates") or name == "fli_search_dates" or name == "search_dates"),
            "fli_search_dates",
        )

        orig_code = resolve_airport_code(str(origin)) or str(origin).upper()
        dest_code = resolve_airport_code(str(destination)) or str(destination).upper()

        args: Dict[str, Any] = {
            "origin": orig_code,
            "destination": dest_code,
            "start_date": start_date,
            "end_date": end_date,
            "trip_duration": trip_duration,
            "is_round_trip": is_round_trip,
            "currency": currency,
        }

        try:
            res = remote_mcp_manager.execute_tool(
                agent_name=self.agent_name,
                tool_name=fli_tool,
                arguments=args,
            )

            if not res.get("success"):
                return {
                    "success": False,
                    "error": res.get("error") or "Failed to search flight dates",
                    "provider": "fli",
                    "dates": [],
                }

            raw_data = res.get("data")
            parsed = extract_raw_json(raw_data)
            dates_list = []
            if isinstance(parsed, dict) and "dates" in parsed:
                dates_list = parsed["dates"]
            elif isinstance(parsed, list):
                dates_list = parsed

            return {
                "success": True,
                "provider": "fli",
                "provider_display_name": "Fli (Google Flights)",
                "origin": orig_code,
                "destination": dest_code,
                "dates": dates_list,
                "count": len(dates_list),
                "date_range": f"{start_date} to {end_date}",
            }
        except Exception as e:
            logger.error(f"[{self.agent_name}] search_dates exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": "fli",
                "dates": [],
            }
