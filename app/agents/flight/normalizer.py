import json
from typing import Any, Dict, List, Optional
from app.schemas.flight import FlightSegment, FlightLayover, NormalizedFlightOffer


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


IATA_AIRLINE_DESIGNATORS: Dict[str, str] = {
    "6E": "IndiGo",
    "AI": "Air India",
    "IX": "Air India Express",
    "SG": "SpiceJet",
    "UK": "Vistara",
    "QP": "Akasa Air",
    "G8": "Go First",
    "I5": "AirAsia India",
    "BA": "British Airways",
    "EY": "Etihad Airways",
    "EK": "Emirates",
    "QR": "Qatar Airways",
    "LH": "Lufthansa",
}


def resolve_carrier_from_flight_number(
    flight_number: Optional[str],
    provider_carrier: Optional[str] = None,
) -> tuple[str, Optional[str]]:
    """
    Validate airline designators against flight numbers.
    Uses provider-supplied airline information as primary source.
    Validates airline designators against flight numbers where reliable (e.g. 6E -> IndiGo, AI -> Air India, IX -> Air India Express).
    Does not silently substitute an airline name.
    Returns (resolved_carrier, note_if_discrepancy).
    """
    if not flight_number:
        return provider_carrier or "Unknown", None

    clean_fn = str(flight_number).strip().upper()
    prefix = ""
    for code in sorted(IATA_AIRLINE_DESIGNATORS.keys(), key=len, reverse=True):
        if clean_fn.startswith(code):
            prefix = code
            break

    expected_airline = IATA_AIRLINE_DESIGNATORS.get(prefix) if prefix else None

    if not provider_carrier or provider_carrier == "Unknown":
        if expected_airline:
            return expected_airline, None
        return "Unknown", None

    if expected_airline:
        prov_clean = provider_carrier.strip()
        if expected_airline.lower() == prov_clean.lower():
            return prov_clean, None

        if prefix in ("6E", "AI", "IX", "SG", "UK", "QP"):
            discrepancy = (
                f"Flight {flight_number} designator '{prefix}' designates '{expected_airline}', "
                f"while provider reported '{prov_clean}'."
            )
            return expected_airline, discrepancy

    return provider_carrier, None


def _parse_legs(
    legs_data: List[Dict[str, Any]],
    origin_hint: str = "",
    dest_hint: str = "",
    parent_airline: str = "Unknown",
) -> tuple[List[FlightSegment], List[FlightLayover]]:
    """Parse legs array into segments and calculate layovers between them."""
    segments: List[FlightSegment] = []
    layovers: List[FlightLayover] = []

    for i, leg in enumerate(legs_data):
        fn = leg.get("flight_number")
        raw_carrier = leg.get("carrier") or parent_airline
        resolved_carrier, _ = resolve_carrier_from_flight_number(fn, raw_carrier)
        carrier_code = leg.get("carrier_code") or (fn[:2].upper() if fn and len(fn) >= 2 else None)

        seg = FlightSegment(
            carrier=resolved_carrier,
            carrier_code=carrier_code,
            flight_number=fn,
            aircraft=leg.get("aircraft"),
            origin=leg.get("departure") or origin_hint,
            destination=leg.get("arrival") or dest_hint,
            departure_time=leg.get("departure_time", ""),
            departure_date=leg.get("departure_date"),
            departure_timezone=None,  # OctoTrip provides local wall-clock times
            arrival_time=leg.get("arrival_time", ""),
            arrival_date=leg.get("arrival_date"),
            arrival_timezone=None,
            duration_minutes=leg.get("duration_minutes"),
        )
        segments.append(seg)

        # Connection layover to next leg
        if i < len(legs_data) - 1:
            next_leg = legs_data[i + 1]
            layover_airport = leg.get("arrival") or next_leg.get("departure", "")
            layover_min = None
            try:
                from datetime import datetime

                arr_d = leg.get("arrival_date")
                arr_t = leg.get("arrival_time")
                dep_d = next_leg.get("departure_date")
                dep_t = next_leg.get("departure_time")
                if arr_d and arr_t and dep_d and dep_t:
                    t1 = datetime.strptime(f"{arr_d} {arr_t}", "%Y-%m-%d %H:%M")
                    t2 = datetime.strptime(f"{dep_d} {dep_t}", "%Y-%m-%d %H:%M")
                    diff = int((t2 - t1).total_seconds() // 60)
                    if diff >= 0:
                        layover_min = diff
            except Exception:
                pass

            layovers.append(
                FlightLayover(
                    airport=layover_airport,
                    duration_minutes=layover_min,
                    duration_seconds=(layover_min * 60) if layover_min is not None else None,
                )
            )

    return segments, layovers


def _validate_airport_route(
    out_origin: str,
    out_dest: str,
    ret_origin: Optional[str],
    ret_dest: Optional[str],
    origin_hint: str,
    dest_hint: str,
    is_round_trip: bool,
) -> tuple[bool, Optional[str]]:
    """
    Validate outbound and return airport codes independently.
    Preserves strict distinction between GOI (Dabolim) and GOX (Manohar Mopa),
    and Jaipur International Airport (JAI) vs other regional airports.
    """
    route_match = True
    notes: List[str] = []

    req_orig = (origin_hint or "").upper().strip()
    req_dest = (dest_hint or "").upper().strip()
    act_orig = (out_origin or "").upper().strip()
    act_dest = (out_dest or "").upper().strip()

    # 1. Outbound origin validation
    if req_orig and act_orig and req_orig != act_orig:
        route_match = False
        notes.append(f"Outbound origin mismatch: requested '{req_orig}', flight departs '{act_orig}'.")

    # 2. Outbound destination validation
    if req_dest == "GOI":
        if act_dest == "GOX":
            route_match = False
            notes.append(
                "Airport mismatch: requested Dabolim Airport (GOI, South Goa), "
                "but flight arrives at Manohar International Airport (GOX, Mopa, North Goa). "
                "GOI and GOX are distinct airports ~60km apart."
            )
        elif act_dest != "GOI":
            route_match = False
            notes.append(f"Destination mismatch: requested Dabolim (GOI), flight arrives '{act_dest}'.")
        else:
            notes.append("Confirmed arrival at Dabolim Airport (GOI, South Goa).")
    elif req_dest == "GOX":
        if act_dest == "GOI":
            route_match = False
            notes.append(
                "Airport mismatch: requested Manohar International Airport (GOX, Mopa, North Goa), "
                "but flight arrives at Dabolim Airport (GOI, South Goa). "
                "GOI and GOX are distinct airports ~60km apart."
            )
        elif act_dest != "GOX":
            route_match = False
            notes.append(f"Destination mismatch: requested Mopa (GOX), flight arrives '{act_dest}'.")
        else:
            notes.append("Confirmed arrival at Manohar International Airport (GOX, Mopa, North Goa).")
    elif req_dest in {"JAI", "JAIPUR"}:
        if act_dest != "JAI":
            route_match = False
            notes.append(
                f"Destination mismatch: requested Jaipur International Airport (JAI), "
                f"but flight arrives at '{act_dest}'."
            )
        else:
            notes.append("Confirmed arrival at Jaipur International Airport (JAI).")
    elif req_dest in {"GOA"}:
        if act_dest == "GOI":
            notes.append("Arrives at Dabolim Airport (GOI, South Goa).")
        elif act_dest == "GOX":
            notes.append("Arrives at Manohar International Airport (GOX, Mopa, North Goa).")
    elif req_dest and act_dest and req_dest != act_dest:
        route_match = False
        notes.append(f"Destination mismatch: requested '{req_dest}', flight arrives '{act_dest}'.")

    # 3. Inbound / Return route validation (independently validated)
    if is_round_trip:
        if not ret_origin or not ret_dest:
            route_match = False
            notes.append("Return journey segments are missing or incomplete.")
        else:
            act_ret_orig = ret_origin.upper().strip()
            act_ret_dest = ret_dest.upper().strip()

            # Return origin should match destination
            if req_dest in {"GOI", "GOX"} and act_ret_orig != req_dest:
                route_match = False
                notes.append(
                    f"Return departure mismatch: requested departure from '{req_dest}', "
                    f"return flight departs '{act_ret_orig}'."
                )
            elif req_dest in {"JAI", "JAIPUR"} and act_ret_orig != "JAI":
                route_match = False
                notes.append(
                    f"Return departure mismatch: requested departure from Jaipur International Airport (JAI), "
                    f"return flight departs '{act_ret_orig}'."
                )
            elif req_dest and act_ret_orig != req_dest:
                route_match = False
                notes.append(
                    f"Return departure mismatch: expected departure from '{req_dest}', "
                    f"return flight departs '{act_ret_orig}'."
                )

            # Return destination should match original origin
            if req_orig and act_ret_dest != req_orig:
                route_match = False
                notes.append(
                    f"Return destination mismatch: requested return to '{req_orig}', "
                    f"return flight arrives '{act_ret_dest}'."
                )

    return route_match, (" ".join(notes) if notes else None)


def _parse_baggage_str(baggage_raw: Any) -> tuple[str, str, str]:
    """Parse raw baggage string into (overall, cabin, checked)."""
    if baggage_raw is not None and str(baggage_raw).strip():
        b_str = str(baggage_raw).strip()
        b_lower = b_str.lower()
        if "15" in b_lower:
            cabin = "7 kg cabin baggage included"
            checked = "15 kg checked baggage included"
        elif "no checked" in b_lower or "0 kg" in b_lower or (("cabin only" in b_lower or "cabin baggage only" in b_lower) and "checked" not in b_lower):
            cabin = "7 kg cabin baggage included"
            checked = "0 kg (No checked bag included)"
        elif "checked" in b_lower:
            cabin = "7 kg cabin baggage included"
            checked = b_str
        else:
            cabin = b_str
            checked = "Checked baggage policy depends on airline fare rules"
        return b_str, cabin, checked
    return "Baggage information unavailable", "Cabin baggage allowance unverified", "Checked baggage allowance unverified"


def _extract_offer_baggage(
    item: Dict[str, Any],
    outbound: Dict[str, Any],
    return_obj: Optional[Dict[str, Any]],
    is_round_trip: bool,
    missing_fields: List[str],
) -> Dict[str, Optional[str]]:
    out_leg_baggage = None
    if outbound.get("legs") and isinstance(outbound["legs"], list) and len(outbound["legs"]) > 0:
        out_leg_baggage = outbound["legs"][0].get("baggage")

    in_leg_baggage = None
    if isinstance(return_obj, dict) and return_obj.get("legs") and isinstance(return_obj["legs"], list) and len(return_obj["legs"]) > 0:
        in_leg_baggage = return_obj["legs"][0].get("baggage")

    out_b_raw = outbound.get("baggage") or out_leg_baggage or item.get("baggage")
    in_b_raw = (return_obj.get("baggage") if isinstance(return_obj, dict) else None) or in_leg_baggage or item.get("baggage")

    out_b_val, out_cabin, out_checked = _parse_baggage_str(out_b_raw)
    if is_round_trip and return_obj:
        in_b_val, in_cabin, in_checked = _parse_baggage_str(in_b_raw)
    else:
        in_b_val, in_cabin, in_checked = None, None, None

    if not out_b_raw and not item.get("baggage"):
        missing_fields.append("baggage")

    if is_round_trip and in_b_val and (out_b_val != in_b_val or out_checked != in_checked):
        overall_b = f"Outbound: {out_b_val} | Return: {in_b_val}"
        overall_cabin = f"Outbound: {out_cabin} | Return: {in_cabin}"
        overall_checked = f"Outbound: {out_checked} | Return: {in_checked}"
    else:
        overall_b = out_b_val
        overall_cabin = out_cabin
        overall_checked = out_checked

    return {
        "baggage": overall_b,
        "cabin_baggage": overall_cabin,
        "checked_baggage": overall_checked,
        "outbound_baggage": out_b_val,
        "inbound_baggage": in_b_val,
        "outbound_cabin_baggage": out_cabin,
        "outbound_checked_baggage": out_checked,
        "inbound_cabin_baggage": in_cabin,
        "inbound_checked_baggage": in_checked,
    }


def normalize_octotrip_flight(
    item: Dict[str, Any],
    origin_hint: str = "",
    dest_hint: str = "",
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    currency: str = "INR",
) -> NormalizedFlightOffer:
    """Normalize a single flight result from OctoTrip MCP (one-way or round-trip)."""
    if not isinstance(item, dict):
        raise ValueError("Invalid flight item: expected a dictionary.")

    outbound = item.get("outbound", {}) or {}
    outbound_legs = outbound.get("legs", []) or []
    parent_airline = item.get("airline") or "Unknown"

    segments, layovers = _parse_legs(outbound_legs, origin_hint, dest_hint, parent_airline)

    # Inbound / Return handling: OctoTrip uses 'return', fallback to 'inbound'
    return_obj = item.get("return") or item.get("inbound")
    inbound_segments: List[FlightSegment] = []
    inbound_layovers: List[FlightLayover] = []
    is_round_trip = False

    ret_dep_date = None
    ret_arr_date = None
    ret_dep_time = None
    ret_arr_time = None
    ret_origin = None
    ret_dest = None
    inbound_dur = None
    inbound_stops = 0

    if isinstance(return_obj, dict) and return_obj.get("legs") and len(return_obj.get("legs", [])) > 0:
        is_round_trip = True
        inbound_legs = return_obj.get("legs", [])
        inbound_segments, inbound_layovers = _parse_legs(
            inbound_legs,
            origin_hint=dest_hint,
            dest_hint=origin_hint,
            parent_airline=parent_airline,
        )
        inbound_dur = return_obj.get("duration_minutes") or sum(
            s.duration_minutes or 0 for s in inbound_segments
        )
        inbound_stops = return_obj.get("stops", max(0, len(inbound_segments) - 1))
        ret_dep_date = return_obj.get("departure_date")
        ret_arr_date = return_obj.get("arrival_date")
        ret_dep_time = return_obj.get("departure_time")
        ret_arr_time = return_obj.get("arrival_time")
        ret_origin = return_obj.get("departure") or (inbound_segments[0].origin if inbound_segments else None)
        ret_dest = return_obj.get("arrival") or (inbound_segments[-1].destination if inbound_segments else None)

    # Flight numbers
    flight_numbers = item.get("flight_numbers", [])
    if not flight_numbers and segments:
        flight_numbers = [s.flight_number for s in segments if s.flight_number]
    if is_round_trip and inbound_segments:
        inbound_fns = [s.flight_number for s in inbound_segments if s.flight_number]
        for fn in inbound_fns:
            if fn not in flight_numbers:
                flight_numbers.append(fn)

    primary_fn = flight_numbers[0] if flight_numbers else None

    # Origins & destinations & offer identification
    out_origin = outbound.get("departure") or (segments[0].origin if segments else origin_hint)
    out_dest = outbound.get("arrival") or (segments[-1].destination if segments else dest_hint)
    adults_cnt = int(item.get("adults") or adults or 1)
    offer_id = str(item.get("id") or f"octo_{item.get('gate', 'direct')}_{'_'.join(flight_numbers)}")

    # Booking URL: Ensure each booking redirect corresponds to the specific offer ID
    booking_url = item.get("booking_url")
    if not booking_url or not str(booking_url).startswith("http"):
        booking_url = f"https://flights.octotrip.com/offers/{offer_id}?origin={out_origin}&dest={out_dest}&adults={adults_cnt}"
    is_bookable = bool(booking_url and str(booking_url).startswith("http"))

    # Missing fields tracking
    missing_fields = []

    # Baggage: extract separate outbound and inbound baggage allowances
    bag_info = _extract_offer_baggage(item, outbound, return_obj, is_round_trip, missing_fields)

    # Fare type
    fare_type_val = item.get("fare_type") or item.get("trip_class")
    if not fare_type_val:
        missing_fields.append("fare_type")

    # Timezones & price verification timestamp (OctoTrip local wall-clock)
    missing_fields.append("departure_timezone")
    missing_fields.append("arrival_timezone")
    if not item.get("price_verification_timestamp"):
        missing_fields.append("price_verification_timestamp")
    from datetime import datetime
    price_ts = item.get("price_verification_timestamp") or datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Dates
    dep_date = outbound.get("departure_date")
    arr_date = outbound.get("arrival_date")
    is_overnight = False
    date_change_days = 0
    if dep_date and arr_date:
        try:
            d1 = datetime.strptime(dep_date, "%Y-%m-%d")
            d2 = datetime.strptime(arr_date, "%Y-%m-%d")
            date_change_days = (d2 - d1).days
            is_overnight = date_change_days > 0
        except Exception:
            pass

    # Durations: KEEP OUTBOUND AND INBOUND DURATIONS SEPARATE!
    # DO NOT CALCULATE TOTAL FLIGHT DURATION BY ADDING OUTBOUND AND RETURN DURATIONS!
    outbound_dur = outbound.get("duration_minutes") or sum(s.duration_minutes or 0 for s in segments)
    outbound_dur_formatted = f"{outbound_dur // 60}h {outbound_dur % 60}m" if outbound_dur else ""
    inbound_dur_formatted = f"{inbound_dur // 60}h {inbound_dur % 60}m" if inbound_dur else ""

    if is_round_trip and outbound_dur_formatted and inbound_dur_formatted:
        duration_formatted = f"Outbound: {outbound_dur_formatted}, Return: {inbound_dur_formatted}"
        total_duration_minutes = outbound_dur  # Outbound flight duration
    elif outbound_dur:
        total_duration_minutes = outbound_dur
        duration_formatted = outbound_dur_formatted
    else:
        total_duration_minutes = item.get("total_duration_minutes") or 0
        duration_formatted = f"{total_duration_minutes // 60}h {total_duration_minutes % 60}m" if total_duration_minutes else ""

    # Stops
    outbound_stops = outbound.get("stops", max(0, len(segments) - 1))
    total_stops = outbound_stops + inbound_stops

    # Origins & destinations
    out_origin = outbound.get("departure") or (segments[0].origin if segments else origin_hint)
    out_dest = outbound.get("arrival") or (segments[-1].destination if segments else dest_hint)

    # Route matching validation
    route_match, airport_notes = _validate_airport_route(
        out_origin=out_origin,
        out_dest=out_dest,
        ret_origin=ret_origin,
        ret_dest=ret_dest,
        origin_hint=origin_hint,
        dest_hint=dest_hint,
        is_round_trip=is_round_trip,
    )

    # Pricing: round-trip price is explicitly tracked so it is never presented as one-way
    raw_price = item.get("price") or item.get("total_price")
    price_val = None
    if raw_price is not None:
        try:
            price_val = float(raw_price)
        except (ValueError, TypeError):
            price_val = None
    total_rt_price = price_val if is_round_trip else None

    # Passenger counts
    adults_cnt = int(item.get("adults") or adults or 1)
    children_cnt = int(item.get("children") or children or 0)
    infants_cnt = int(item.get("infants") or infants or 0)
    passenger_cnt = adults_cnt + children_cnt + infants_cnt

    offer_id = f"octo_{item.get('gate', 'direct')}_{'_'.join(flight_numbers)}"

    outbound_carriers = [s.carrier for s in segments if s.carrier and s.carrier != "Unknown"]
    inbound_carriers = [s.carrier for s in inbound_segments if s.carrier and s.carrier != "Unknown"]
    outbound_airline = outbound_carriers[0] if outbound_carriers else parent_airline
    inbound_airline = inbound_carriers[0] if inbound_carriers else None

    # Never combine two airlines into one ambiguous label.
    # Outbound and return airline names are preserved and displayed independently.
    offer_airline = outbound_airline

    return NormalizedFlightOffer(
        provider="flight_octotrip",
        provider_flight_id=offer_id,
        airline=offer_airline,
        airline_code=item.get("airline_code"),
        outbound_airline=outbound_airline,
        inbound_airline=inbound_airline,
        flight_number=primary_fn,
        flight_numbers=flight_numbers,
        origin=out_origin,
        destination=out_dest,
        departure_time=outbound.get("departure_time", ""),
        departure_date=dep_date,
        departure_timezone=None,
        arrival_time=outbound.get("arrival_time", ""),
        arrival_date=arr_date,
        arrival_timezone=None,
        is_direct=bool(item.get("is_direct", len(segments) <= 1)),
        stops=outbound_stops,
        outbound_stops=outbound_stops,
        inbound_stops=inbound_stops,
        total_stops=total_stops,
        is_round_trip=is_round_trip,
        is_overnight=is_overnight,
        date_change_days=date_change_days,
        segments=segments,
        layovers=layovers,
        inbound_segments=inbound_segments,
        inbound_layovers=inbound_layovers,
        outbound_duration_minutes=outbound_dur,
        inbound_duration_minutes=inbound_dur,
        outbound_duration_formatted=outbound_dur_formatted,
        inbound_duration_formatted=inbound_dur_formatted,
        return_origin=ret_origin,
        return_destination=ret_dest,
        return_departure_time=ret_dep_time,
        return_departure_date=ret_dep_date,
        return_arrival_time=ret_arr_time,
        return_arrival_date=ret_arr_date,
        total_round_trip_price=total_rt_price,
        route_match=route_match,
        airport_notes=airport_notes,
        duration_formatted=duration_formatted,
        total_duration_minutes=total_duration_minutes,
        price=price_val,
        currency=item.get("currency") or currency or "INR",
        fare_type=fare_type_val,
        baggage=bag_info["baggage"],
        cabin_baggage=bag_info["cabin_baggage"],
        checked_baggage=bag_info["checked_baggage"],
        outbound_baggage=bag_info["outbound_baggage"],
        inbound_baggage=bag_info["inbound_baggage"],
        outbound_cabin_baggage=bag_info["outbound_cabin_baggage"],
        outbound_checked_baggage=bag_info["outbound_checked_baggage"],
        inbound_cabin_baggage=bag_info["inbound_cabin_baggage"],
        inbound_checked_baggage=bag_info["inbound_checked_baggage"],
        passenger_count=passenger_cnt,
        adults=adults_cnt,
        children=children_cnt,
        infants=infants_cnt,
        booking_url=booking_url,
        is_bookable=is_bookable,
        price_verification_timestamp=price_ts,
        missing_fields=missing_fields,
        raw_metadata=item,
    )


def rank_flight_offers(offers: List[NormalizedFlightOffer]) -> Dict[str, List[NormalizedFlightOffer]]:
    """
    Rank flight offers according to four standard dimensions using the actual total price:
    1. Cheapest: lowest total round-trip price (or one-way price). Strict monotonic order.
    2. Fastest: shortest outbound journey duration (never summing outbound + return).
    3. Fewest Stops: lowest total stops first, then lowest price.
    4. Best Value: composite trade-off between price, duration, and convenience.
    """
    if not offers:
        return {
            "best_value": [],
            "cheapest": [],
            "fastest": [],
            "fewest_stops": [],
        }

    def _effective_price(f: NormalizedFlightOffer) -> float:
        if f.is_round_trip and f.total_round_trip_price is not None:
            return f.total_round_trip_price
        return f.price if f.price is not None else float("inf")

    # 1. Cheapest: Sort strictly by effective price
    cheapest = sorted(offers, key=lambda f: (f.price is None, _effective_price(f)))
    for rank, offer in enumerate(cheapest, 1):
        offer.rankings["cheapest_rank"] = rank

    def _journey_duration(f: NormalizedFlightOffer) -> Optional[int]:
        if f.is_round_trip and f.outbound_duration_minutes and f.inbound_duration_minutes:
            return f.outbound_duration_minutes + f.inbound_duration_minutes
        return f.outbound_duration_minutes if f.outbound_duration_minutes is not None else f.total_duration_minutes

    # 2. Fastest: Sort by total journey duration (outbound + inbound for RT, or outbound for OW)
    fastest = sorted(
        offers,
        key=lambda f: (_journey_duration(f) is None, _journey_duration(f) if _journey_duration(f) is not None else float("inf")),
    )
    for rank, offer in enumerate(fastest, 1):
        offer.rankings["fastest_rank"] = rank

    # 3. Fewest stops (total stops: outbound + inbound, tie-break on price)
    fewest_stops = sorted(
        offers,
        key=lambda f: (f.total_stops, f.price is None, _effective_price(f)),
    )
    for rank, offer in enumerate(fewest_stops, 1):
        offer.rankings["fewest_stops_rank"] = rank

    # 4. Best Overall Value Composite
    valid_prices = [_effective_price(f) for f in offers if f.price is not None]
    min_p = min(valid_prices) if valid_prices else 1.0
    max_p = max(valid_prices) if valid_prices else 1.0
    p_range = (max_p - min_p) if (max_p > min_p) else 1.0

    valid_durs = [_journey_duration(f) for f in offers if _journey_duration(f)]
    min_d = min(valid_durs) if valid_durs else 1.0
    max_d = max(valid_durs) if valid_durs else 1.0
    d_range = (max_d - min_d) if (max_d > min_d) else 1.0

    for offer in offers:
        cur_p = _effective_price(offer)
        p_norm = ((cur_p - min_p) / p_range) if offer.price is not None else 1.0
        dur_v = _journey_duration(offer)
        d_norm = (
            ((dur_v - min_d) / d_range)
            if dur_v
            else 1.0
        )
        stop_penalty = offer.total_stops * 0.15

        # 55% Price, 30% Duration, 15% Stops
        composite = (0.55 * p_norm) + (0.30 * d_norm) + stop_penalty
        offer.best_value_score = round(composite, 3)

    best_value = sorted(
        offers,
        key=lambda f: (f.best_value_score is None, f.best_value_score if f.best_value_score is not None else float("inf")),
    )
    for rank, offer in enumerate(best_value, 1):
        offer.rankings["best_value_rank"] = rank

    return {
        "best_value": best_value,
        "cheapest": cheapest,
        "fastest": fastest,
        "fewest_stops": fewest_stops,
    }


# =============================================================================
# FLI GOOGLE FLIGHTS MCP NORMALIZATION
# =============================================================================
try:
    from fli.models import Airport
    _AIRPORT_NAME_TO_CODE = {a.value.upper(): a.name for a in Airport}
except Exception:
    _AIRPORT_NAME_TO_CODE = {}


def resolve_fli_airport_code(name_or_code: Any) -> str:
    """Resolve an airport name or code to a 3-letter IATA code."""
    if not name_or_code:
        return ""
    s = str(name_or_code).strip()
    if len(s) == 3 and s.isalpha():
        return s.upper()
    up = s.upper()
    if up in _AIRPORT_NAME_TO_CODE:
        return _AIRPORT_NAME_TO_CODE[up]
    for name, code in _AIRPORT_NAME_TO_CODE.items():
        if name in up or up in name:
            return code
    return s[:3].upper()


def _format_fli_dt(val: Any) -> tuple[str, str]:
    """Extract (time 'HH:MM', date 'YYYY-MM-DD') from a datetime or ISO string."""
    if val is None:
        return "", ""
    if hasattr(val, "strftime"):
        return val.strftime("%H:%M"), val.strftime("%Y-%m-%d")
    s = str(val).strip()
    if "T" in s:
        parts = s.split("T")
        return parts[1][:5], parts[0]
    if " " in s:
        parts = s.split(" ")
        return parts[1][:5], parts[0]
    return s, ""


def _parse_fli_leg(leg: Dict[str, Any], default_orig: str, default_dest: str) -> FlightSegment:
    dep_time_str, dep_date_str = _format_fli_dt(leg.get("departure_time"))
    arr_time_str, arr_date_str = _format_fli_dt(leg.get("arrival_time"))
    orig_code = resolve_fli_airport_code(leg.get("departure_airport") or leg.get("departure_airport_name")) or default_orig
    dest_code = resolve_fli_airport_code(leg.get("arrival_airport") or leg.get("arrival_airport_name")) or default_dest
    carrier_name = leg.get("airline") or "Unknown"
    carrier_code = leg.get("airline_code") or ""
    flight_num = str(leg.get("flight_number") or "").strip()
    aircraft = leg.get("aircraft") or ""
    duration = leg.get("duration")

    full_fn = f"{carrier_code}{flight_num}" if (carrier_code and flight_num and not flight_num.startswith(carrier_code)) else (flight_num or carrier_code)

    return FlightSegment(
        carrier=carrier_name,
        carrier_code=carrier_code or None,
        flight_number=full_fn or None,
        aircraft=aircraft or None,
        origin=orig_code.upper(),
        destination=dest_code.upper(),
        departure_time=dep_time_str,
        departure_date=dep_date_str or None,
        departure_timezone=None,
        arrival_time=arr_time_str,
        arrival_date=arr_date_str or None,
        arrival_timezone=None,
        duration_minutes=duration,
    )


def normalize_fli_flight(
    item: Dict[str, Any],
    origin_hint: str,
    dest_hint: str,
    preferred_currency: str = "INR",
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    is_round_trip_requested: bool = False,
) -> NormalizedFlightOffer:
    """Normalize a single flight result from Fli Google Flights MCP (one-way or round-trip)."""
    if not isinstance(item, dict):
        raise ValueError("Invalid flight item: expected a dictionary.")

    legs = item.get("legs", []) or []
    primary_airline = item.get("primary_airline") or (legs[0].get("airline_code") if legs else "")
    primary_airline_name = item.get("primary_airline_name") or (legs[0].get("airline") if legs else "Unknown")
    booking_url = item.get("booking_url")

    # Round trip detection
    is_round_trip = bool(item.get("return_flight") or item.get("is_round_trip") or is_round_trip_requested)

    outbound_legs_raw: List[Dict[str, Any]] = []
    inbound_legs_raw: List[Dict[str, Any]] = []

    if is_round_trip and len(legs) > 1:
        # Split legs between outbound and inbound
        reached_destination = False
        for leg in legs:
            dep_code = resolve_fli_airport_code(leg.get("departure_airport") or leg.get("departure_airport_name"))
            if reached_destination or (dep_code == dest_hint.upper()):
                reached_destination = True
                inbound_legs_raw.append(leg)
            else:
                outbound_legs_raw.append(leg)
                arr_code = resolve_fli_airport_code(leg.get("arrival_airport") or leg.get("arrival_airport_name"))
                if arr_code == dest_hint.upper():
                    reached_destination = True
        if not inbound_legs_raw and len(legs) > 1:
            mid = len(legs) // 2
            outbound_legs_raw = legs[:mid]
            inbound_legs_raw = legs[mid:]
    else:
        outbound_legs_raw = legs
        inbound_legs_raw = []

    # Parse outbound segments
    outbound_segments: List[FlightSegment] = [
        _parse_fli_leg(l, origin_hint, dest_hint) for l in outbound_legs_raw
    ]

    # Parse outbound layovers
    outbound_layovers: List[FlightLayover] = []
    for i in range(len(outbound_segments) - 1):
        layover_airport = outbound_segments[i].destination
        outbound_layovers.append(FlightLayover(airport=layover_airport))

    # Parse inbound segments & layovers
    inbound_segments: List[FlightSegment] = [
        _parse_fli_leg(l, dest_hint, origin_hint) for l in inbound_legs_raw
    ]
    inbound_layovers: List[FlightLayover] = []
    for i in range(len(inbound_segments) - 1):
        layover_airport = inbound_segments[i].destination
        inbound_layovers.append(FlightLayover(airport=layover_airport))

    # Calculate durations
    outbound_dur = sum(s.duration_minutes or 0 for s in outbound_segments)
    inbound_dur = sum(s.duration_minutes or 0 for s in inbound_segments) if inbound_segments else None
    total_dur = outbound_dur + (inbound_dur or 0)

    dur_h = total_dur // 60
    dur_m = total_dur % 60
    duration_formatted = f"{dur_h}h {dur_m}m" if dur_h > 0 else f"{dur_m}m"

    out_dur_h = outbound_dur // 60
    out_dur_m = outbound_dur % 60
    outbound_dur_formatted = f"{out_dur_h}h {out_dur_m}m" if out_dur_h > 0 else f"{out_dur_m}m"

    inbound_dur_formatted = ""
    if inbound_dur is not None:
        in_dur_h = inbound_dur // 60
        in_dur_m = inbound_dur % 60
        inbound_dur_formatted = f"{in_dur_h}h {in_dur_m}m" if in_dur_h > 0 else f"{in_dur_m}m"

    # Flight numbers
    flight_numbers: List[str] = []
    for s in outbound_segments + inbound_segments:
        if s.flight_number and s.flight_number not in flight_numbers:
            flight_numbers.append(s.flight_number)
    primary_fn = flight_numbers[0] if flight_numbers else None

    # Origin and destination
    out_orig = outbound_segments[0].origin if outbound_segments else origin_hint.upper()
    out_dest = outbound_segments[-1].destination if outbound_segments else dest_hint.upper()
    dep_time = outbound_segments[0].departure_time if outbound_segments else ""
    dep_date = outbound_segments[0].departure_date if outbound_segments else None
    arr_time = outbound_segments[-1].arrival_time if outbound_segments else ""
    arr_date = outbound_segments[-1].arrival_date if outbound_segments else None

    # Inbound endpoints
    ret_orig = inbound_segments[0].origin if inbound_segments else None
    ret_dest = inbound_segments[-1].destination if inbound_segments else None
    ret_dep_time = inbound_segments[0].departure_time if inbound_segments else None
    ret_dep_date = inbound_segments[0].departure_date if inbound_segments else None
    ret_arr_time = inbound_segments[-1].arrival_time if inbound_segments else None
    ret_arr_date = inbound_segments[-1].arrival_date if inbound_segments else None

    # Stops
    outbound_stops = max(0, len(outbound_segments) - 1)
    inbound_stops = max(0, len(inbound_segments) - 1)
    total_stops = outbound_stops + inbound_stops
    is_direct = (outbound_stops == 0 and inbound_stops == 0)

    # Overnight check
    is_overnight = False
    date_change_days = 0
    from datetime import datetime
    if dep_date and arr_date:
        try:
            d1 = datetime.strptime(dep_date, "%Y-%m-%d")
            d2 = datetime.strptime(arr_date, "%Y-%m-%d")
            date_change_days = (d2 - d1).days
            is_overnight = date_change_days > 0
        except Exception:
            pass

    price = float(item.get("price") or 0.0)
    currency = item.get("currency") or preferred_currency

    clean_dep = dep_time.replace(":", "") if dep_time else "0000"
    offer_id = f"fli_{primary_airline}_{primary_fn or 'opt'}_{clean_dep}"

    detected_cabin = None
    if legs and isinstance(legs[0], dict):
        detected_cabin = legs[0].get("cabin")
    if not detected_cabin:
        detected_cabin = item.get("cabin_class") or item.get("trip_class")
    
    clean_cabin = str(detected_cabin).strip().upper() if detected_cabin else "ECONOMY"
    if "BUSINESS" in clean_cabin:
        fare_type = "Business Class"
        cabin_baggage = "Cabin baggage (up to 10kg) included"
        checked_baggage = "Checked baggage (2 pieces up to 35kg) included"
        baggage = "Checked baggage (35kg) + Cabin baggage (10kg) included"
    elif "FIRST" in clean_cabin:
        fare_type = "First Class"
        cabin_baggage = "Cabin baggage (up to 12kg) included"
        checked_baggage = "Checked baggage (up to 40kg) included"
        baggage = "Checked baggage (40kg) + Cabin baggage (12kg) included"
    elif "PREMIUM" in clean_cabin:
        fare_type = "Premium Economy"
        cabin_baggage = "Cabin baggage (up to 7kg) included"
        checked_baggage = "Checked baggage (up to 20kg) included"
        baggage = "Checked baggage (20kg) + Cabin baggage (7kg) included"
    else:
        fare_type = "Economy"
        cabin_baggage = "Cabin baggage (up to 7kg) included"
        checked_baggage = "Checked baggage (up to 15kg) included"
        baggage = "15kg checked + 7kg cabin baggage included"

    return NormalizedFlightOffer(
        provider="fli",
        provider_flight_id=offer_id,
        airline=primary_airline_name,
        airline_code=primary_airline or None,
        flight_number=primary_fn,
        flight_numbers=flight_numbers,
        origin=out_orig,
        destination=out_dest,
        departure_time=dep_time,
        departure_date=dep_date,
        departure_timezone=None,
        arrival_time=arr_time,
        arrival_date=arr_date,
        arrival_timezone=None,
        is_direct=is_direct,
        stops=outbound_stops,
        is_round_trip=bool(inbound_segments),
        is_overnight=is_overnight,
        date_change_days=date_change_days,
        segments=outbound_segments,
        layovers=outbound_layovers,
        inbound_segments=inbound_segments,
        inbound_layovers=inbound_layovers,
        outbound_duration_minutes=outbound_dur,
        inbound_duration_minutes=inbound_dur,
        outbound_duration_formatted=outbound_dur_formatted,
        inbound_duration_formatted=inbound_dur_formatted,
        outbound_airline=primary_airline_name,
        inbound_airline=(inbound_segments[0].carrier if inbound_segments else None),
        return_origin=ret_orig,
        return_destination=ret_dest,
        return_departure_time=ret_dep_time,
        return_departure_date=ret_dep_date,
        return_arrival_time=ret_arr_time,
        return_arrival_date=ret_arr_date,
        outbound_stops=outbound_stops,
        inbound_stops=inbound_stops,
        total_stops=total_stops,
        total_round_trip_price=price if bool(inbound_segments) else None,
        route_match=True,
        airport_notes=None,
        duration_formatted=duration_formatted,
        total_duration_minutes=total_dur,
        price=price,
        currency=currency,
        fare_type=fare_type,
        baggage=baggage,
        cabin_baggage=cabin_baggage,
        checked_baggage=checked_baggage,
        outbound_baggage=baggage,
        inbound_baggage=baggage if inbound_segments else None,
        outbound_cabin_baggage=cabin_baggage,
        outbound_checked_baggage=checked_baggage,
        inbound_cabin_baggage=cabin_baggage if inbound_segments else None,
        inbound_checked_baggage=checked_baggage if inbound_segments else None,
        passenger_count=adults + children + infants,
        adults=adults,
        children=children,
        infants=infants,
        booking_url=booking_url or f"https://www.google.com/travel/flights?q=Flights%20from%20{out_orig}%20to%20{out_dest}&curr={currency}",
        is_bookable=bool(booking_url and str(booking_url).startswith("http")),
        price_verification_timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        missing_fields=[],
        rankings={},
        raw_metadata=item,
    )
