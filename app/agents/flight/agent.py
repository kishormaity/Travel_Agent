import time
from typing import Any, Dict, List, Optional
from loguru import logger
from app.mcp.remote import remote_mcp_manager
from app.schemas.agents import FlightAgentOutput
from app.schemas.flight import NormalizedFlightOffer
from app.agents.flight.normalizer import (
    extract_raw_json,
    normalize_octotrip_flight,
    rank_flight_offers,
)
from app.core.observability import (
    log_specialist_task_start,
    log_specialist_task_end,
    sanitize_secrets,
)


import threading
from app.services.request_normalizer import resolve_airport_code


class FlightAgent:
    """
    Specialized agent responsible for searching, normalizing, and ranking flight options
    exclusively via the OctoTrip Flight MCP Provider.
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
        limit: int = 10,
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

        # Specific guardrail: Reject or auto-correct invalid UDI code to UDR
        if destination == "UDI":
            logger.warning(f"[{self.agent_name}] Intercepted invalid airport code 'UDI'. Corrected to canonical 'UDR' (Udaipur).")
            destination = "UDR"
        if origin == "UDI":
            logger.warning(f"[{self.agent_name}] Intercepted invalid airport code 'UDI'. Corrected to canonical 'UDR' (Udaipur).")
            origin = "UDR"

        logger.info(
            f"[{self.agent_name}] Initiating OctoTrip flight search: origin={origin} (from '{raw_origin}'), "
            f"dest={destination} (from '{raw_destination}'), dep_date={dep_date}, return_date={ret_date}, "
            f"adults={adults}, currency={preferred_currency}, task_id={task_id}"
        )

        all_normalized_offers: List[NormalizedFlightOffer] = []
        raw_response: Any = None
        error_msg: Optional[str] = None

        if not origin or not destination:
            return FlightAgentOutput(
                success=False,
                error="Both origin/departure and destination/arrival airport codes or city names are required. At least one search filter must specify valid route endpoints.",
                summary=f"Missing origin or destination for flight search (origin={origin}, destination={destination}).",
                flights=[],
                data={"count": 0, "flights": [], "ranked": {}},
                execution_time_ms=(time.time() - start_time) * 1000.0,
            )

        if not dep_date:
            return FlightAgentOutput(
                success=False,
                error="Departure flight date is required for flight search.",
                summary="Missing departure flight date for flight search.",
                flights=[],
                data={"count": 0, "flights": [], "ranked": {}},
                execution_time_ms=(time.time() - start_time) * 1000.0,
            )

        # ---------------------------------------------------------------------
        # 0. Check In-Memory Deduplication Cache (Prevents 50-61s re-executions)
        # ---------------------------------------------------------------------
        cache_key = f"{origin}:{destination}:{dep_date}:{ret_date}:{adults}:{children}:{infants}:{trip_class}:{preferred_currency}"
        if not bypass_cache:
            with self._cache_lock:
                if cache_key in self._flight_cache:
                    cached_time, cached_out = self._flight_cache[cache_key]
                    if time.time() - cached_time < 1800.0:  # 30-minute valid TTL
                        logger.info(
                            f"[{self.agent_name}] Cache HIT for flight search {cache_key} "
                            f"(age: {time.time() - cached_time:.1f}s, offers: {len(cached_out.flights)})"
                        )
                        # Return cached result with updated execution time
                        return cached_out.model_copy(update={"execution_time_ms": (time.time() - start_time) * 1000.0})

        # ---------------------------------------------------------------------
        # 1. Initialize and locate OctoTrip MCP tool
        # ---------------------------------------------------------------------
        remote_mcp_manager.ensure_initialized()

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

        t0 = log_specialist_task_start(
            task_id=task_id,
            specialist_name=self.agent_name,
            selected_mcp_server=self.mcp_provider,
            selected_tool=octotrip_tool,
            arguments=ot_args,
        )

        # ---------------------------------------------------------------------
        # Bounded Retries with Exponential Backoff for Remote OctoTrip GDS calls
        # ---------------------------------------------------------------------
        max_retries = 2
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

                err_detail = str(ot_res.get("error", ""))
                is_timeout = any(term in err_detail.lower() for term in ("timeout", "504", "502", "503", "gateway"))

                if attempt < max_retries and is_timeout:
                    retry_wait = 1.5 * (attempt + 1)
                    logger.warning(
                        f"[{self.agent_name}] OctoTrip transient delay/timeout (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{err_detail}. Retrying in {retry_wait:.1f}s..."
                    )
                    time.sleep(retry_wait)
                    continue
                else:
                    break

            except Exception as e:
                err_detail = str(e)
                is_timeout = any(term in err_detail.lower() for term in ("timeout", "504", "502", "503", "gateway"))
                if attempt < max_retries and is_timeout:
                    retry_wait = 1.5 * (attempt + 1)
                    logger.warning(
                        f"[{self.agent_name}] OctoTrip exception (attempt {attempt + 1}/{max_retries + 1}): "
                        f"{e}. Retrying in {retry_wait:.1f}s..."
                    )
                    time.sleep(retry_wait)
                    continue
                error_msg = str(e)
                logger.error(f"[{self.agent_name}] OctoTrip execution error: {e}")
                break

        try:
            if ot_res and ot_res.get("success") and ot_res.get("data"):
                raw_response = ot_res["data"]
                parsed_ot = extract_raw_json(raw_response)
                ot_results: List[Dict[str, Any]] = []

                if isinstance(parsed_ot, dict) and "results" in parsed_ot:
                    ot_results = parsed_ot["results"]
                elif isinstance(parsed_ot, list):
                    for item in parsed_ot:
                        if isinstance(item, dict) and "results" in item:
                            ot_results.extend(item["results"])
                        elif isinstance(item, dict):
                            ot_results.append(item)

                for item in ot_results:
                    offer = normalize_octotrip_flight(
                        item,
                        origin_hint=origin,
                        dest_hint=destination,
                        adults=adults,
                        children=children,
                        infants=infants,
                        currency=preferred_currency,
                    )
                    all_normalized_offers.append(offer)

                log_specialist_task_end(
                    task_id=task_id,
                    specialist_name=self.agent_name,
                    selected_mcp_server=self.mcp_provider,
                    selected_tool=octotrip_tool,
                    start_time=t0,
                    status="COMPLETED",
                    raw_response={"count": len(all_normalized_offers), "preview": ot_results[:2]},
                )
            else:
                err = (ot_res.get("error") if ot_res else None) or error_msg or "No data returned from OctoTrip MCP"
                error_msg = str(err)
                log_specialist_task_end(
                    task_id=task_id,
                    specialist_name=self.agent_name,
                    selected_mcp_server=self.mcp_provider,
                    selected_tool=octotrip_tool,
                    start_time=t0,
                    status="FAILED",
                    raw_response=ot_res,
                )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{self.agent_name}] OctoTrip response processing error: {e}")
            log_specialist_task_end(
                task_id=task_id,
                specialist_name=self.agent_name,
                selected_mcp_server=self.mcp_provider,
                selected_tool=octotrip_tool,
                start_time=t0,
                status="FAILED",
                exception=e,
            )

        # ---------------------------------------------------------------------
        # 2. Ranking and Output Synthesis
        # ---------------------------------------------------------------------
        # Filter/prioritize valid route matches first
        matching_offers = [o for o in all_normalized_offers if o.route_match]
        non_matching_offers = [o for o in all_normalized_offers if not o.route_match]

        # Rank all offers
        ranked = rank_flight_offers(all_normalized_offers)
        
        # Primary presentation prioritizes matching offers ranked by best_value
        ranked_matching = [o for o in ranked["best_value"] if o.route_match]
        ranked_non_matching = [o for o in ranked["best_value"] if not o.route_match]
        ordered_offers = ranked_matching + ranked_non_matching if ranked_matching else ranked["best_value"]
        flight_dicts = [offer.model_dump() for offer in ordered_offers]

        elapsed_ms = (time.time() - start_time) * 1000.0
        category_notes: List[str] = []

        if all_normalized_offers:
            success = True
            error_val = None
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
                route_validation_note = " Note: Some results had airport/route mismatches (e.g. GOI vs GOX) and have been flagged."

            if is_rt and best_opt.inbound_airline and best_opt.inbound_airline != best_opt.outbound_airline:
                best_airline_str = f"Outbound: {best_opt.outbound_airline}, Return: {best_opt.inbound_airline}"
            else:
                best_airline_str = best_opt.outbound_airline or best_opt.airline

            category_notes = []
            if best_opt.provider_flight_id == cheapest_opt.provider_flight_id == fastest_opt.provider_flight_id:
                category_notes.append(
                    f"Option {best_opt.flight_number} ({best_airline_str}) is simultaneously ranked as Best Value, Cheapest, and Fastest "
                    f"because it combines the lowest verified round-trip fare of {best_opt.price} {best_opt.currency} "
                    f"with the shortest overall journey duration ({duration_details}) and 0 layover stops."
                )
            elif best_opt.provider_flight_id == cheapest_opt.provider_flight_id:
                category_notes.append(
                    f"Option {best_opt.flight_number} ({best_airline_str}) is both Best Value and Cheapest due to offering the lowest verified round-trip fare ({best_opt.price} {best_opt.currency}) with optimal travel time."
                )
            elif best_opt.provider_flight_id == fastest_opt.provider_flight_id:
                category_notes.append(
                    f"Option {best_opt.flight_number} ({best_airline_str}) is both Best Value and Fastest due to offering the shortest journey duration."
                )
            category_note_str = f" {' '.join(category_notes)}" if category_notes else ""

            summary = (
                f"Found {len(all_normalized_offers)} {trip_type_str} flight option(s) between "
                f"{origin} and {destination} via OctoTrip. "
                f"Best Value: {best_airline_str} ({best_opt.flight_number or 'N/A'}) at {best_opt.price} {best_opt.currency} {price_suffix} ({duration_details}); "
                f"Cheapest: {cheapest_opt.outbound_airline or cheapest_opt.airline} at {cheapest_opt.price} {cheapest_opt.currency} {price_suffix}; "
                f"Fastest: {fastest_opt.outbound_airline or fastest_opt.airline} ({fastest_opt.duration_formatted} total).{category_note_str}{route_validation_note}"
            )
        else:
            if error_msg:
                success = False
                error_val = error_msg
                summary = f"Unable to retrieve flights between {origin} and {destination}. Provider error: {error_msg}"
            else:
                success = True
                error_val = None
                summary = f"No commercial flights available between {origin} and {destination} on {dep_date}."

        ranked_highlights = {}
        if all_normalized_offers and ordered_offers:
            ranked_highlights = {
                "best_value": best_opt.model_dump(),
                "cheapest": cheapest_opt.model_dump(),
                "fastest": fastest_opt.model_dump(),
            }

        output_obj = FlightAgentOutput(
            success=success,
            error=error_val,
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
                "provider": self.mcp_provider,
                "raw_response": raw_response,
            },
            execution_time_ms=elapsed_ms,
        )

        if success and all_normalized_offers:
            with self._cache_lock:
                self._flight_cache[cache_key] = (time.time(), output_obj)

        return output_obj
