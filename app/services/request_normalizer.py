import re
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, Dict, Any, List
from loguru import logger
from pydantic import BaseModel, Field


class NormalizedTravelRequest(BaseModel):
    """Normalized structured travel request representation."""
    origin: Optional[str] = None
    origin_airport: Optional[str] = None
    destination: Optional[str] = None
    destination_airport: Optional[str] = None
    destinations: List[str] = Field(default_factory=list)
    destination_airports: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None
    adults: int = 1
    children: int = 0
    infants: int = 0
    total_budget: Optional[float] = None
    per_person_budget: Optional[float] = None
    currency: str = "INR"
    is_multi_city: bool = False
    is_international: bool = False
    preferences: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


# ==============================================================================
# Canonical Airport and City Mapping
# ==============================================================================

KNOWN_AIRPORTS: Dict[str, Tuple[str, str]] = {
    "DEL": ("Delhi", "India"),
    "BOM": ("Mumbai", "India"),
    "CCU": ("Kolkata", "India"),
    "BLR": ("Bengaluru", "India"),
    "MAA": ("Chennai", "India"),
    "HYD": ("Hyderabad", "India"),
    "GOI": ("Goa", "India"),
    "GOX": ("Goa", "India"),
    "JAI": ("Jaipur", "India"),
    "UDR": ("Udaipur", "India"),
    "JDH": ("Jodhpur", "India"),
    "COK": ("Kochi", "India"),
    "VNS": ("Varanasi", "India"),
    "ATQ": ("Amritsar", "India"),
    "SXR": ("Srinagar", "India"),
    "BKK": ("Bangkok", "Thailand"),
    "DMK": ("Bangkok", "Thailand"),
    "HKT": ("Phuket", "Thailand"),
    "CNX": ("Chiang Mai", "Thailand"),
    "KBV": ("Krabi", "Thailand"),
    "SIN": ("Singapore", "Singapore"),
    "DXB": ("Dubai", "United Arab Emirates"),
    "AUH": ("Abu Dhabi", "United Arab Emirates"),
    "DOH": ("Doha", "Qatar"),
    "LHR": ("London", "United Kingdom"),
    "LGW": ("London", "United Kingdom"),
    "CDG": ("Paris", "France"),
    "FCO": ("Rome", "Italy"),
    "BCN": ("Barcelona", "Spain"),
    "AMS": ("Amsterdam", "Netherlands"),
    "FRA": ("Frankfurt", "Germany"),
    "NRT": ("Tokyo", "Japan"),
    "HND": ("Tokyo", "Japan"),
    "KIX": ("Osaka", "Japan"),
    "SYD": ("Sydney", "Australia"),
    "MEL": ("Melbourne", "Australia"),
    "JFK": ("New York", "United States"),
    "EWR": ("New York", "United States"),
}

CITY_TO_AIRPORT: Dict[str, str] = {
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "bengaluru": "BLR",
    "bangalore": "BLR",
    "chennai": "MAA",
    "madras": "MAA",
    "hyderabad": "HYD",
    "goa": "GOI",
    "jaipur": "JAI",
    "udaipur": "UDR",
    "jodhpur": "JDH",
    "jodhur": "JDH",
    "kochi": "COK",
    "cochin": "COK",
    "varanasi": "VNS",
    "amritsar": "ATQ",
    "srinagar": "SXR",
    "bangkok": "BKK",
    "phuket": "HKT",
    "chiang mai": "CNX",
    "krabi": "KBV",
    "singapore": "SIN",
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "doha": "DOH",
    "london": "LHR",
    "paris": "CDG",
    "rome": "FCO",
    "barcelona": "BCN",
    "amsterdam": "AMS",
    "frankfurt": "FRA",
    "tokyo": "NRT",
    "osaka": "KIX",
    "kyoto": "KIX",
    "sydney": "SYD",
    "melbourne": "MEL",
    "new york": "JFK",
}

CO_TERMINAL_AIRPORTS: Dict[str, set] = {
    "BKK": {"BKK", "DMK"},
    "DMK": {"BKK", "DMK"},
    "GOI": {"GOI", "GOX"},
    "GOX": {"GOI", "GOX"},
    "NRT": {"NRT", "HND"},
    "HND": {"NRT", "HND"},
    "LHR": {"LHR", "LGW", "LCY", "STN", "LTN"},
    "LGW": {"LHR", "LGW", "LCY", "STN", "LTN"},
    "JFK": {"JFK", "EWR", "LGA"},
    "EWR": {"JFK", "EWR", "LGA"},
}

MONTH_MAP: Dict[str, int] = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


# ==============================================================================
# Destination Equivalence and Normalization
# ==============================================================================

def normalize_city_name(raw: str) -> str:
    """Extracts primary city name from strings like 'Bangkok, Thailand' -> 'Bangkok'."""
    if not raw:
        return ""
    # Strip country if comma separated
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return ""
    city = parts[0]
    # Remove parenthesized IATA codes like 'Delhi (DEL)'
    city = re.sub(r"\s*\([a-zA-Z]{3}\)", "", city).strip()
    return city


def get_country_context(raw: str) -> Optional[str]:
    """Extracts country context from strings like 'Bangkok, Thailand' -> 'thailand'."""
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) >= 2:
        return parts[-1].lower()
    city_lower = parts[0].lower() if parts else ""
    # Check if city has known country in airport map
    for iata, (c_name, country) in KNOWN_AIRPORTS.items():
        if c_name.lower() == city_lower:
            return country.lower()
    return None


def are_destinations_equivalent(dest1: str, dest2: str, _is_subpart: bool = False) -> bool:
    """
    Evaluates whether two destination strings refer to the same city/destination.
    Treats 'Bangkok' and 'Bangkok, Thailand' as equivalent.
    Never equates genuinely different single destinations (e.g. Bangkok vs Phuket).
    In multi-city contexts, recognizes if a single city is part of a multi-city list.
    """
    if not dest1 or not dest2:
        return False
    s1 = dest1.strip().lower()
    s2 = dest2.strip().lower()
    if s1 == s2:
        return True

    city1 = normalize_city_name(dest1).lower()
    city2 = normalize_city_name(dest2).lower()

    if not city1 or not city2:
        return False

    if city1 == city2:
        country1 = get_country_context(dest1)
        country2 = get_country_context(dest2)
        if country1 and country2 and country1 != country2:
            return False
        return True

    # Check known aliases/spellings
    aliases = {
        "calcutta": "kolkata",
        "kolkata": "calcutta",
        "bombay": "mumbai",
        "mumbai": "bombay",
        "bangalore": "bengaluru",
        "bengaluru": "bangalore",
        "madras": "chennai",
        "chennai": "madras",
        "new delhi": "delhi",
        "delhi": "new delhi",
    }
    if aliases.get(city1) == city2 or aliases.get(city2) == city1:
        return True

    # Multi-city component awareness (e.g., 'Jaipur' matching 'Jaipur and Udaipur')
    if not _is_subpart:
        parts1 = [p.strip() for p in re.split(r"\s+(?:and|&|then)\s+", dest1, flags=re.IGNORECASE) if p.strip()]
        parts2 = [p.strip() for p in re.split(r"\s+(?:and|&|then)\s+", dest2, flags=re.IGNORECASE) if p.strip()]
        if len(parts1) > 1 or len(parts2) > 1:
            for p1 in parts1:
                for p2 in parts2:
                    if p1 and p2 and are_destinations_equivalent(p1, p2, _is_subpart=True):
                        return True

    return False


def are_airports_equivalent(iata1: str, iata2: str) -> bool:
    """Evaluates whether two IATA airport codes match directly or are co-terminals in the same metropolitan area."""
    if not iata1 or not iata2:
        return False
    i1 = iata1.strip().upper()
    i2 = iata2.strip().upper()
    if i1 == i2:
        return True
    if i1 in CO_TERMINAL_AIRPORTS and i2 in CO_TERMINAL_AIRPORTS[i1]:
        return True
    return False


AIRPORT_CODE_ALIASES: Dict[str, str] = {
    "UDI": "UDR",  # UDI is Uberlandia, Brazil. In Indian queries for Udaipur, resolve to UDR
    "UDAIPUR": "UDR",
    "JODHPUR": "JDH",
    "JODHUR": "JDH",
    "JAIPUR": "JAI",
}


def resolve_airport_code(city_or_iata: str, context_hint: Optional[str] = None) -> Optional[str]:
    """
    Resolves a 3-letter IATA airport code from an airport code or city name.
    Specifically guarantees Udaipur resolves to UDR and invalid codes like UDI are corrected to UDR.
    """
    if not city_or_iata:
        return None
    cleaned = city_or_iata.strip().upper()

    # Intercept known hallucinations and city names passed as codes
    if cleaned in AIRPORT_CODE_ALIASES:
        logger.warning(
            f"[AirportResolution] Intercepted airport code/alias '{cleaned}'. "
            f"Resolving to canonical '{AIRPORT_CODE_ALIASES[cleaned]}'."
        )
        return AIRPORT_CODE_ALIASES[cleaned]

    if len(cleaned) == 3 and cleaned in KNOWN_AIRPORTS:
        return cleaned

    city_lower = normalize_city_name(city_or_iata).lower()
    if city_lower in CITY_TO_AIRPORT:
        return CITY_TO_AIRPORT[city_lower]

    # Check typos
    city_typos = {
        "jodhur": "JDH",
        "jodhpu": "JDH",
        "jodpur": "JDH",
        "udipur": "UDR",
        "udaipr": "UDR",
        "jaipue": "JAI",
    }
    if city_lower in city_typos:
        return city_typos[city_lower]

    if context_hint:
        hint_lower = context_hint.strip().lower()
        if "udaipur" in hint_lower or "udr" in hint_lower:
            return "UDR"
        if "jodhpur" in hint_lower or "jodhur" in hint_lower:
            return "JDH"
        if "jaipur" in hint_lower:
            return "JAI"

    return None


# ==============================================================================
# Robust Date Extraction Engine
# ==============================================================================

class DateExtractionResult:
    def __init__(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        duration_days: Optional[int] = None,
        is_explicit: bool = False,
        error: Optional[str] = None,
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.duration_days = duration_days
        self.is_explicit = is_explicit
        self.error = error


def _parse_month(m_str: str) -> Optional[int]:
    if not m_str:
        return None
    return MONTH_MAP.get(m_str.strip().lower())


def extract_trip_dates(text: str) -> DateExtractionResult:
    """
    Extracts, normalizes, and validates trip dates from user queries.
    Preserves exact dates explicitly supplied by user.
    Enforces end_date > start_date.
    Calculates duration consistently from requested dates.
    Never silently replaces a valid user-provided date with an inferred date.
    """
    if not text:
        return DateExtractionResult(error="Empty input text")

    clean_text = text.strip()
    sum_lower = clean_text.lower()

    # 1. Check for explicit duration in days
    explicit_duration = None
    dur_match = re.search(r"\b(\d+)\s*[-–\s]?day\b", sum_lower)
    if dur_match:
        try:
            explicit_duration = int(dur_match.group(1))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Pattern A: ISO 8601 format: YYYY-MM-DD to YYYY-MM-DD
    # -------------------------------------------------------------------------
    iso_match = re.search(
        r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s*(?:to|until|-|–)\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b",
        clean_text,
    )
    if iso_match:
        y1, m1, d1, y2, m2, d2 = map(int, iso_match.groups())
        try:
            dt1 = date(y1, m1, d1)
            dt2 = date(y2, m2, d2)
            if dt2 <= dt1:
                return DateExtractionResult(
                    error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                )
            dur = (dt2 - dt1).days
            return DateExtractionResult(
                start_date=dt1.isoformat(),
                end_date=dt2.isoformat(),
                duration_days=dur,
                is_explicit=True,
            )
        except ValueError as ve:
            return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # -------------------------------------------------------------------------
    # Pattern B: DD/MM/YYYY to DD/MM/YYYY
    # -------------------------------------------------------------------------
    dmy_match = re.search(
        r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\s*(?:to|until|-|–)\s*(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b",
        clean_text,
    )
    if dmy_match:
        d1, m1, y1, d2, m2, y2 = map(int, dmy_match.groups())
        try:
            dt1 = date(y1, m1, d1)
            dt2 = date(y2, m2, d2)
            if dt2 <= dt1:
                return DateExtractionResult(
                    error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                )
            dur = (dt2 - dt1).days
            return DateExtractionResult(
                start_date=dt1.isoformat(),
                end_date=dt2.isoformat(),
                duration_days=dur,
                is_explicit=True,
            )
        except ValueError as ve:
            return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # -------------------------------------------------------------------------
    # Pattern C: Month names on both dates:
    # "from 10 December to 17 December 2026"
    # "10 December 2026 to 17 December 2026"
    # "28 December 2026 to 4 January 2027" (crossing months and years)
    # "25 November to 2 December 2026" (crossing months)
    # -------------------------------------------------------------------------
    both_months_match = re.search(
        r"\b(?:from\s+)?(\d{1,2})\s+([a-zA-Z]+)(?:\s*,?\s*(\d{4}))?\s*(?:to|until|-|–)\s*(\d{1,2})\s+([a-zA-Z]+)(?:\s*,?\s*(\d{4}))\b",
        clean_text,
        re.IGNORECASE,
    )
    if both_months_match:
        d1_str, m1_str, y1_str, d2_str, m2_str, y2_str = both_months_match.groups()
        m1 = _parse_month(m1_str)
        m2 = _parse_month(m2_str)
        if m1 and m2:
            d1 = int(d1_str)
            d2 = int(d2_str)
            y2 = int(y2_str)
            if y1_str:
                y1 = int(y1_str)
            else:
                # If months cross year boundary (Dec -> Jan), year 1 is y2 - 1
                if m1 == 12 and m2 == 1:
                    y1 = y2 - 1
                else:
                    y1 = y2
            try:
                dt1 = date(y1, m1, d1)
                dt2 = date(y2, m2, d2)
                if dt2 <= dt1:
                    return DateExtractionResult(
                        error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                    )
                dur = (dt2 - dt1).days
                return DateExtractionResult(
                    start_date=dt1.isoformat(),
                    end_date=dt2.isoformat(),
                    duration_days=dur,
                    is_explicit=True,
                )
            except ValueError as ve:
                return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # -------------------------------------------------------------------------
    # Pattern D: Month first on both dates:
    # "from December 10 to December 17, 2026"
    # "December 28, 2026 to January 4, 2027"
    # -------------------------------------------------------------------------
    month_first_both_match = re.search(
        r"\b(?:from\s+)?([a-zA-Z]+)\s+(\d{1,2})(?:\s*,?\s*(\d{4}))?\s*(?:to|until|-|–)\s*([a-zA-Z]+)\s+(\d{1,2})(?:\s*,?\s*(\d{4}))\b",
        clean_text,
        re.IGNORECASE,
    )
    if month_first_both_match:
        m1_str, d1_str, y1_str, m2_str, d2_str, y2_str = month_first_both_match.groups()
        m1 = _parse_month(m1_str)
        m2 = _parse_month(m2_str)
        if m1 and m2:
            d1 = int(d1_str)
            d2 = int(d2_str)
            y2 = int(y2_str)
            y1 = int(y1_str) if y1_str else (y2 - 1 if m1 == 12 and m2 == 1 else y2)
            try:
                dt1 = date(y1, m1, d1)
                dt2 = date(y2, m2, d2)
                if dt2 <= dt1:
                    return DateExtractionResult(
                        error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                    )
                dur = (dt2 - dt1).days
                return DateExtractionResult(
                    start_date=dt1.isoformat(),
                    end_date=dt2.isoformat(),
                    duration_days=dur,
                    is_explicit=True,
                )
            except ValueError as ve:
                return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # -------------------------------------------------------------------------
    # Pattern E: Day range with single month at end:
    # "10 to 17 December 2026" / "10-17 December 2026" / "10–17 December 2026"
    # -------------------------------------------------------------------------
    single_month_end_match = re.search(
        r"\b(?:from\s+)?(\d{1,2})\s*(?:to|until|-|–)\s*(\d{1,2})\s+([a-zA-Z]+)(?:\s*,?\s*(\d{4}))\b",
        clean_text,
        re.IGNORECASE,
    )
    if single_month_end_match:
        d1_str, d2_str, m_str, y_str = single_month_end_match.groups()
        m = _parse_month(m_str)
        if m:
            d1 = int(d1_str)
            d2 = int(d2_str)
            y = int(y_str)
            try:
                dt1 = date(y, m, d1)
                dt2 = date(y, m, d2)
                if dt2 <= dt1:
                    return DateExtractionResult(
                        error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                    )
                dur = (dt2 - dt1).days
                return DateExtractionResult(
                    start_date=dt1.isoformat(),
                    end_date=dt2.isoformat(),
                    duration_days=dur,
                    is_explicit=True,
                )
            except ValueError as ve:
                return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # -------------------------------------------------------------------------
    # Pattern F: Month first with day range:
    # "December 10 to 17, 2026" / "December 10 - 17, 2026"
    # -------------------------------------------------------------------------
    month_first_day_range_match = re.search(
        r"\b(?:from\s+)?([a-zA-Z]+)\s+(\d{1,2})\s*(?:to|until|-|–)\s*(\d{1,2})(?:\s*,?\s*(\d{4}))\b",
        clean_text,
        re.IGNORECASE,
    )
    if month_first_day_range_match:
        m_str, d1_str, d2_str, y_str = month_first_day_range_match.groups()
        m = _parse_month(m_str)
        if m:
            d1 = int(d1_str)
            d2 = int(d2_str)
            y = int(y_str)
            try:
                dt1 = date(y, m, d1)
                dt2 = date(y, m, d2)
                if dt2 <= dt1:
                    return DateExtractionResult(
                        error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                    )
                dur = (dt2 - dt1).days
                return DateExtractionResult(
                    start_date=dt1.isoformat(),
                    end_date=dt2.isoformat(),
                    duration_days=dur,
                    is_explicit=True,
                )
            except ValueError as ve:
                return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # -------------------------------------------------------------------------
    # Pattern G: Single start date with duration or explicit check-out
    # "starting on 10 December 2026", "from 10 December 2026"
    # -------------------------------------------------------------------------
    single_start_match = re.search(
        r"\b(?:starting|beginning|departs?|departing|from)\s+(?:on\s+)?(\d{1,2})\s+([a-zA-Z]+)(?:\s*,?\s*(\d{4}))\b",
        clean_text,
        re.IGNORECASE,
    )
    if single_start_match:
        d1_str, m_str, y_str = single_start_match.groups()
        m = _parse_month(m_str)
        if m:
            d1 = int(d1_str)
            y = int(y_str)
            try:
                dt1 = date(y, m, d1)
                # Check for explicit check-out date
                cout_match = re.search(
                    r"\b(?:check-?out|return|returning|until)\s+(?:on\s+)?(\d{1,2})\s+([a-zA-Z]+)(?:\s*,?\s*(\d{4}))\b",
                    clean_text,
                    re.IGNORECASE,
                )
                if cout_match:
                    cd2_str, cm_str, cy_str = cout_match.groups()
                    cm = _parse_month(cm_str)
                    if cm:
                        dt2 = date(int(cy_str), cm, int(cd2_str))
                        if dt2 <= dt1:
                            return DateExtractionResult(
                                error=f"Invalid date range: end_date ({dt2}) must be strictly after start_date ({dt1})"
                            )
                        dur = (dt2 - dt1).days
                        return DateExtractionResult(
                            start_date=dt1.isoformat(),
                            end_date=dt2.isoformat(),
                            duration_days=dur,
                            is_explicit=True,
                        )

                # If no check-out date, use explicit duration
                if explicit_duration and explicit_duration > 0:
                    dt2 = dt1 + timedelta(days=explicit_duration)
                    return DateExtractionResult(
                        start_date=dt1.isoformat(),
                        end_date=dt2.isoformat(),
                        duration_days=explicit_duration,
                        is_explicit=True,
                    )
                else:
                    return DateExtractionResult(
                        start_date=dt1.isoformat(),
                        end_date=None,
                        duration_days=None,
                        is_explicit=True,
                    )
            except ValueError as ve:
                return DateExtractionResult(error=f"Invalid calendar date: {ve}")

    # No explicit dates could be reliably extracted
    return DateExtractionResult(
        start_date=None,
        end_date=None,
        duration_days=explicit_duration,
        is_explicit=False,
    )


# ==============================================================================
# Full Normalized Travel Request Builder
# ==============================================================================

def normalize_travel_request_from_text(summary: str) -> NormalizedTravelRequest:
    """
    Deterministically normalizes a travel request from natural language text.
    Extracts origin, destination, canonical airports, dates, duration, adults, and budget.
    Never silently replaces user-supplied dates or destinations with hardcoded fallbacks.
    """
    norm_req = NormalizedTravelRequest()
    if not summary:
        return norm_req

    sum_lower = summary.lower()

    # 1. Origin extraction
    origin_match = re.search(
        r"\bfrom\s+([a-zA-Z\s]+?)(?:\s*\(([a-zA-Z]{3})\))?(?:\s+to|\s*,|\s+from|\s+on|\s+starting|\s+between|$)",
        summary,
        re.IGNORECASE,
    )
    if origin_match:
        cand_name = origin_match.group(1).strip()
        cand_iata = origin_match.group(2).upper() if origin_match.group(2) else None
        if cand_iata:
            norm_req.origin_airport = cand_iata
            if cand_iata in KNOWN_AIRPORTS:
                norm_req.origin = KNOWN_AIRPORTS[cand_iata][0]
            else:
                norm_req.origin = cand_name
        elif cand_name:
            norm_req.origin = normalize_city_name(cand_name)
            norm_req.origin_airport = resolve_airport_code(cand_name)

    # Secondary origin check
    if not norm_req.origin:
        for iata, (c_name, _) in KNOWN_AIRPORTS.items():
            if re.search(rf"\b(from\s+{c_name.lower()}|{iata.lower()})\b", sum_lower):
                norm_req.origin = c_name
                norm_req.origin_airport = iata
                break

    # 2. Destination extraction (Single and Multi-City)
    dest_match = re.search(
        r"\bto\s+([a-zA-Z\s,–&-]+?)(?:\s*,?\s*from|\s+on\b|\s+starting\b|\s+with\b|\s+for\b|\s+between\b|$)",
        summary,
        re.IGNORECASE,
    )
    raw_dest_str = dest_match.group(1).strip() if dest_match else None

    multi_cities: List[str] = []
    if raw_dest_str:
        if re.search(r"\b(?:and|&|then)\b", raw_dest_str, re.IGNORECASE):
            potential_stops = re.split(r",\s*(?:and\s+)?|\s+(?:and|&|then)\s+", raw_dest_str, flags=re.IGNORECASE)
            for stop in potential_stops:
                s_clean = stop.strip()
                if not s_clean:
                    continue
                city_norm = normalize_city_name(s_clean)
                if city_norm and len(city_norm) >= 3:
                    country = get_country_context(s_clean)
                    canon = f"{city_norm.title()}, {country.title()}" if country and country != "india" else city_norm.title()
                    if canon not in multi_cities:
                        multi_cities.append(canon)
        else:
            city_norm = normalize_city_name(raw_dest_str)
            if city_norm:
                country = get_country_context(raw_dest_str)
                canon = f"{city_norm.title()}, {country.title()}" if country and country != "india" else city_norm.title()
                multi_cities.append(canon)

    if multi_cities:
        norm_req.destinations = multi_cities
        norm_req.destination_airports = [resolve_airport_code(c) for c in multi_cities if resolve_airport_code(c)]
        if len(multi_cities) > 1:
            norm_req.is_multi_city = True
            norm_req.destination = " and ".join([normalize_city_name(c) for c in multi_cities])
            norm_req.destination_airport = norm_req.destination_airports[0] if norm_req.destination_airports else None
        else:
            norm_req.is_multi_city = False
            norm_req.destination = multi_cities[0]
            norm_req.destination_airport = norm_req.destination_airports[0] if norm_req.destination_airports else None

    # Secondary destination check if still empty
    if not norm_req.destination:
        for iata, (c_name, country) in KNOWN_AIRPORTS.items():
            if re.search(rf"\b(to\s+{c_name.lower()}|{c_name.lower()})\b", sum_lower):
                canon = f"{c_name}, {country}" if country != "India" else c_name
                norm_req.destination = canon
                norm_req.destinations = [canon]
                norm_req.destination_airport = iata
                norm_req.destination_airports = [iata]
                break

    # 3. Dates & Duration extraction via robust date engine
    date_res = extract_trip_dates(summary)
    if date_res.start_date:
        norm_req.start_date = date_res.start_date
    if date_res.end_date:
        norm_req.end_date = date_res.end_date
    if date_res.duration_days:
        norm_req.duration_days = date_res.duration_days
    elif date_res.start_date and date_res.end_date:
        d1 = datetime.strptime(date_res.start_date, "%Y-%m-%d")
        d2 = datetime.strptime(date_res.end_date, "%Y-%m-%d")
        norm_req.duration_days = max(1, (d2 - d1).days)

    # 4. Passengers extraction (adults, children, infants)
    adult_match = re.search(r"(\d+)\s*(?:adults?|passengers?|travelers?|people|persons?)", sum_lower)
    if adult_match:
        norm_req.adults = int(adult_match.group(1))
    elif re.search(r"\b(?:solo|for\s+myself|just\s+me)\b", sum_lower):
        norm_req.adults = 1
    elif re.search(r"\b(?:couple|two\s+of\s+us)\b", sum_lower):
        norm_req.adults = 2
    else:
        norm_req.adults = 2

    child_match = re.search(r"(\d+)\s*(?:child(?:ren)?|kids?)", sum_lower)
    if child_match:
        norm_req.children = int(child_match.group(1))

    infant_match = re.search(r"(\d+)\s*(?:infants?|bab(?:y|ies))", sum_lower)
    if infant_match:
        norm_req.infants = int(infant_match.group(1))

    # 5. Currency & Budget extraction
    if re.search(r"(?:\$|\busd\b)", summary, re.IGNORECASE):
        norm_req.currency = "USD"
    elif re.search(r"(?:€|\beur(?:o)?\b)", summary, re.IGNORECASE):
        norm_req.currency = "EUR"
    elif re.search(r"(?:£|\bgbp\b|\bpounds?\b)", summary, re.IGNORECASE):
        norm_req.currency = "GBP"
    elif re.search(r"\b(?:thb|baht)\b", summary, re.IGNORECASE):
        norm_req.currency = "THB"
    else:
        norm_req.currency = "INR"

    is_per_person = bool(re.search(r"\b(?:per\s+(?:person|traveler|adult|head)|each)\b", summary, re.IGNORECASE))

    budget_match = re.search(
        r"(?:₹|rs\.?|inr|\$|usd|€|eur|£|gbp|thb|budget\s*(?:is|of)?\s*)[\s₹\$€£]*([\d,]+(?:\.\d+)?)",
        summary,
        re.IGNORECASE,
    )
    if budget_match:
        try:
            parsed_amt = float(budget_match.group(1).replace(",", ""))
            total_travelers = max(1, norm_req.adults + norm_req.children)
            if is_per_person:
                norm_req.per_person_budget = parsed_amt
                norm_req.total_budget = round(parsed_amt * total_travelers, 2)
            else:
                norm_req.total_budget = parsed_amt
                norm_req.per_person_budget = round(parsed_amt / total_travelers, 2)
        except Exception:
            norm_req.total_budget = None
            norm_req.per_person_budget = None
    else:
        # Never fabricate a budget if not provided by user
        norm_req.total_budget = None
        norm_req.per_person_budget = None

    return norm_req
