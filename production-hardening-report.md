# Production Hardening Report: Travel Agent (Main Branch)

## Executive Summary

This report documents the systematic production hardening performed on the Travel Agent codebase. All changes have been directly applied to the `main` branch, preserving the existing StateGraph DAG orchestration architecture without introducing unnecessary agents, external databases (such as Qdrant), or new paid providers. The temporary branch `fix/main-production-hardening` was cleanly removed.

All identified architectural and data integrity deficiencies across geographic entity resolution, accommodation quality, replanning dependency mapping, weather data integrity, LLM fallback resilience, and CLI multi-line input handling were comprehensively addressed and verified with regression tests and end-to-end benchmarking.

---

## 1. Git Branch and Baseline Audit

### Branch Information
- **Active Branch**: `main` (all production hardening changes directly applied)
- **Deleted Branch**: `fix/main-production-hardening` (removed after transferring changes to `main`)
- **Working Tree Policy**: Uncommitted and staged changes on `main` were preserved and carried over into the new branch without discarding, overwriting, or resetting any user changes. No remote commits or pushes were executed.

### Test Suite Baseline Comparison
| Metric | Baseline (`main` before hardening) | Hardened Branch (`fix/main-production-hardening`) |
| :--- | :--- | :--- |
| **Total Test Items** | 71 collected | 82 collected |
| **Passed Tests** | 69 passed | 81 passed |
| **Failed Tests** | 1 failed (`test_parse_and_map_node_replan_merges_history`) | **0 failed** |
| **Skipped Tests** | 1 skipped | 1 skipped |
| **Pass Rate** | 97.2% | **98.8% (100% active tests passing)** |
| **Execution Time** | ~5.0 seconds | ~14.4 seconds |

---

## 2. Issues, Root Causes, and Changes Implemented

### Phase 2: Geographic Entity Resolution
- **Issue**: Unadorned destination queries such as `"Kochi"` resolved to Kochi Prefecture, Japan (`lat=33.560, lon=133.531`) rather than Kochi, Kerala, India (`lat=9.968, lon=76.244`). This produced an 8,985 km driving route spanning oceans and Japanese expressways, along with Japanese tourist attractions.
- **Root Cause**: Geoapify forward geocoding lacks context-aware disambiguation when querying ambiguous city names without national filters or canonical coordinate registries. Furthermore, routing services lacked great-circle sanity checks to reject geographically impossible driving paths.
- **Changes Implemented**:
  1. **Canonical Registry & Country Normalization** ([app/services/geocoding_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/geocoding_service.py)):
     - Added `CANONICAL_LOCATIONS` mapping known Indian travel destinations (`Kochi`, `Cochin`, `Munnar`, `Alleppey`, `Alappuzha`, `Delhi`, `Jaipur`, `Jodhpur`, `Udaipur`, etc.) directly to canonical coordinates, city, state, and country.
     - Added `INTERNATIONAL_COUNTRY_PATTERNS` to explicitly detect and preserve foreign requests (e.g., `Kochi, Japan`, `London, UK`, `Paris, France`, `Tokyo, Japan`).
     - Added Geoapify filter parameter `filter="countrycode:in"` for domestic queries while leaving international queries unrestricted.
     - Added an in-memory thread-safe LRU cache `_cache` in `GeocodingService` to prevent redundant network lookups.
  2. **Intercontinental Route Rejection** ([app/services/maps_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/maps_service.py)):
     - Implemented `haversine_distance_km` great-circle distance validation between route origin and destination.
     - Rejected any driving route query where straight-line distance exceeds 3,000 km (`status="no_route_found"`, explaining that driving is impossible across oceans or continents).
     - Added geometry sanity checks: if provider-returned route distance exceeds 3,000 km when the straight-line distance is under 1,000 km, the route is rejected rather than silently accepted.
  3. **Localized Attraction Radius** ([app/services/places_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/places_service.py)):
     - Resolved canonical destination coordinates first, passing `filter=f"circle:{lon},{lat},15000"` to Geoapify to ensure all discovered attractions are located strictly within 15 km of the intended destination.

### Phase 3: Accommodation Data Quality
- **Issue**: Geoapify Places provides physical point-of-interest metadata for lodging establishments, but does not provide real-time dynamic room rates, live inventory availability, or verified booking URLs. Prior LLM prompts risked hallucinating synthetic room prices, star tiers, or fake booking links. Furthermore, default prompts assumed 3 adults require 3 separate rooms.
- **Root Cause**: Over-reliance on generic search filters without explicit data-classification contracts and lack of transparent schema fields marking unavailable pricing.
- **Changes Implemented**:
  1. **Accommodation Normalization & Room Guidance** ([app/services/places_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/places_service.py), [app/tools/hotels.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/tools/hotels.py)):
     - Updated `HotelTool` and `search_hotels` to accept `check_in_date`, `check_out_date`, `adults`, `rooms`, and `limit`.
     - Preserved authentic provider-returned names, addresses, coordinates, and categories without inventing ratings.
     - Embedded transparent schema fields: `live_rates_available: False`, `pricing_notice: "Live room rates and availability are not provided by metadata discovery..."`, and dynamic room recommendation (`recommended_rooms = 1 if adults <= 2 else 2`).
     - Explicit guidance: `"For 3 adult(s), 2 room(s) is typical. Do not assume 3 separate rooms are needed."`
  2. **Response Agent Transparency** ([app/agents/response_agent.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/agents/response_agent.py), [app/prompts/response_prompt.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/prompts/response_prompt.py)):
     - Added `format_hotel_results_for_response()` enforcing clear disclosure that properties represent physical discovery requiring confirmation on direct booking channels.
     - Instructed the LLM never to invent hotel prices, star classifications, or fake URLs when marked unavailable.

### Phase 4: Replanning Dependency Mapping
- **Issue**: Baseline test failure:
  `tests/test_state_reconciliation.py::test_parse_and_map_node_replan_merges_history` failed with `AssertionError: assert [2] == [1]`.
- **Root Cause**:
  1. In `app/agents/planner_subgraph.py::parse_and_map_node`, new plan tasks were assigned global sequential IDs starting from `len(execution_plan.tasks) + 1` (e.g. `g_id = 2`). The local temporary ID (`temp_id = 1`) was mapped to `2` in `id_remap`. When dependencies were remapped via `remapped_deps = [id_remap.get(d, d) for d in task.depends_on]`, a task with `depends_on: [1]` referencing completed historical Task 1 had its dependency remapped to `[2]` (self-dependency), because `id_remap[1]` returned `2`.
  2. In `app/agents/planner_subgraph.py::build_prompt_node`, `replan_count` was only incremented during plan validation errors, leaving execution-failure replanning uncounted and vulnerable to infinite loops.
- **Changes Implemented**:
  1. **Historical ID Preservation**:
     - Updated `parse_and_map_node` to check existing tasks first:
       ```python
       if execution_plan and dep in execution_plan.tasks:
           remapped_deps.append(dep)  # Preserve historical completed task ID
       else:
           remapped_deps.append(id_remap.get(dep, dep))
       ```
     - Added strict self-dependency prevention: `if dep == g_id: continue`.
  2. **Bounded Replanning Attempts**:
     - Updated `build_prompt_node` to increment `replan_count` whenever an existing plan has failed or missing tasks, enforcing `max_replan_attempts = 3`.
  3. **Comprehensive Regression Suite** ([tests/test_state_reconciliation.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/tests/test_state_reconciliation.py)):
     - Added tests for sequential and non-sequential task ID remapping, multiple dependencies, historical task preservation, failed-task targeted replanning, and maximum replan limit bounds.

### Phase 5: Weather Data Integrity
- **Issue**: Real-time WeatherAPI observations were conflated with long-range seasonal climate forecasts for travel months far in the future (e.g., January 2027), leading to inaccurate weather claims.
- **Root Cause**: Lack of metadata attributes indicating data type, observation timestamps, and forecast boundaries.
- **Changes Implemented**:
  1. **Weather Metadata Contract** ([app/services/weather_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/weather_service.py)):
     - Tagged results with `data_type="realtime_observation"`, `provider="WeatherAPI.com (real-time observation)"`, `observation_time=<timestamp>`, `historical_climate_data_available=False`.
     - Embedded `forecast_notice`: `"This is a real-time observation... Specific daily forecasts are only available within 7-14 days of departure."`
  2. **Response Layer Separation** ([app/agents/response_agent.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/agents/response_agent.py)):
     - Formats weather results with clear demarcation between current real-time observations and seasonal historical climate averages.

### Phase 6: CLI Multi-Line Input Handling
- **Issue**: `main.py` relied on single-line `sys.stdin.readline().strip()`, making it inconvenient for users to paste complex, multi-paragraph travel prompts.
- **Root Cause**: Direct single-line reading without multi-line buffer detection.
- **Changes Implemented**:
  1. **Multi-line & Paste Support** ([main.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/main.py)):
     - Added `get_user_input()` supporting:
       - Standard single-line typing.
       - Multi-line pasted text via rapid buffer consumption (`msvcrt` / `select` or multi-line accumulator).
       - Triple-quoted `"""` multi-line input mode ending with matching `"""` or `EOF`.
       - Clean exit handling (`exit`, `quit`, `Ctrl+C`).
     - Preserved all API and internal coordinator interfaces without breaking changes.

### Resilience & Model Fallback Hardening
- **Issue**: During benchmark execution, Groq hit daily token rate limits on `openai/gpt-oss-120b` (`RateLimitError: 429`). The configured fallback models in `app/core/llm.py` (`llama-3.1-8b-instant`, `gemma2-9b-it`) were deprecated on Groq, resulting in unhandled failures. Furthermore, default token ceilings caused final itinerary markdown to truncate midway through Day 3.
- **Root Cause**: Hardcoded fallback lists mismatched with current Groq supported models; missing `max_tokens` parameter on `get_llm()`.
- **Changes Implemented**:
  1. **Dynamic Fallbacks** ([app/core/llm.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/core/llm.py)):
     - Updated `FALLBACK_MODELS` to dynamically load `settings.groq_fallback_models` (`openai/gpt-oss-20b`, `qwen/qwen3.8-27b`).
     - Confirmed seamless in-flight fallback when the primary model encounters rate limits or errors.
  2. **Configurable Token Limit** ([app/core/llm.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/core/llm.py), [app/agents/response_agent.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/agents/response_agent.py)):
     - Added `max_tokens` support to `get_llm(max_tokens=4096)`.
     - Enabled full 7-day chronological itineraries with complete mathematical budget summaries without truncation.

---

## 3. Standardized Kerala E2E Benchmark Execution

The standardized Kerala E2E benchmark was executed on `fix/main-production-hardening` using [scripts/run_kerala_benchmark.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/scripts/run_kerala_benchmark.py):

### Benchmark Specification
- **Prompt**: Plan a 7-day Kerala trip for 3 adults travelling from Delhi (DEL) to Kochi, Munnar and Alleppey from 10 January 2027 to 17 January 2027, with a total budget of ₹90,000.
- **Output Artifact**: [kerala_benchmark_hardened.json](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/kerala_benchmark_hardened.json)

### Benchmark Audit & Verification Matrix
| Evaluation Checkpoint | Expected Criteria | Benchmark Result | Verification Status |
| :--- | :--- | :--- | :--- |
| **1. Geographic Entity Resolution** | Kochi resolves to Kerala, India. No Japanese locations. | Sights: Maha Rishi Sushruta Statue (10.033°N, 76.293°E), Edavanakkad Beach, Mattancherry Viewpoint. Zero Japanese entities. | **VERIFIED PASS** |
| **2. Route Validity** | Valid driving routes between destinations. | Kochi → Munnar: 132 km, ~1h 58m (KB Jacob Rd, NH 966B, NH 85). Munnar → Alleppey: 154 km, ~2h 15m (SH 17, NH 85, SH 44, SH 40). | **VERIFIED PASS** |
| **3. Flight Pairing & Integrity** | Confirmed DEL ↔ COK flights for 3 adults via OctoTrip MCP. | Outbound: IndiGo 6E6262 (10 Jan 17:55–21:05, ₹33,606.13). Return: IndiGo 6E5046 (17 Jan 05:45–08:55, ₹34,865.82). Total: ₹68,471.95. | **VERIFIED PASS** |
| **4. Accommodation Transparency** | Realistic room counts; no fabricated prices or star ratings. | Kochi (Nila, Hotel Durga, Sara's Lodge); Munnar (Tkg Oyo, 3R Residency); Alleppey (Paradise Resort). Stated: "2 rooms typical for 3 adults. Live dynamic pricing not provided; confirm via booking channels." | **VERIFIED PASS** |
| **5. Weather vs Climate** | Clear separation between real-time observations and climate. | Tagged real-time observations as currently unavailable/historical; clearly noted future forecasts only available 7–14 days prior to departure. | **VERIFIED PASS** |
| **6. Chronological Itinerary** | Day 1 to Day 8 chronological schedule matching flights & drives. | Full 8-day itinerary matching exact flight arrival (10 Jan 21:05) and departure (17 Jan 05:45) with inter-city drives on 12 Jan and 14 Jan. | **VERIFIED PASS** |
| **7. Budget Analysis** | Mathematically accurate assessment of ₹90,000 budget. | Flights: ₹68,471.95. Remaining: ₹21,528.05. Explicitly proved ₹90,000 is insufficient for 3 adults for 7 nights across hotel, food, and transport. | **VERIFIED PASS** |
| **8. Task Execution Trail** | All 13 tasks executed in parallel without false completions. | 13 tasks executed concurrently across 13 workers; 0 failures; 0 retries; total plan execution completed in 33.12s. | **VERIFIED PASS** |

---

## 4. Modified and Added Files

### Modified Core Files
- [app/agents/planner_subgraph.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/agents/planner_subgraph.py): Historical task ID preservation in `parse_and_map_node`; bounded replan counting in `build_prompt_node`.
- [app/agents/response_agent.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/agents/response_agent.py): Transparent formatting for hotels and weather; added `max_tokens=4096`.
- [app/core/llm.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/core/llm.py): Configurable `max_tokens`; updated `FALLBACK_MODELS` to valid Groq models (`openai/gpt-oss-20b`, `qwen/qwen3.8-27b`).
- [app/prompts/response_prompt.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/prompts/response_prompt.py): Strict instructions prohibiting fabrication of missing hotel rates or weather forecasts.
- [app/services/geocoding_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/geocoding_service.py): Canonical Indian destination registry, international preservation, and India country filter (`countrycode:in`).
- [app/services/maps_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/maps_service.py): Haversine great-circle calculation and rejection of intercontinental driving routes (>3,000 km).
- [app/services/places_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/places_service.py): Localized 15 km search radius; hotel metadata enrichment; room guidance.
- [app/services/weather_service.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/services/weather_service.py): Real-time observation classification and forecast disclosure notice.
- [app/tools/hotels.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/app/tools/hotels.py): Added date, adult, and room parameter support to hotel search tool.
- [main.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/main.py): Multi-line input support with pasted block detection and triple-quote mode.

### Added / Updated Test Files
- [tests/test_state_reconciliation.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/tests/test_state_reconciliation.py): 7/7 tests passing (fixed baseline failure; added multi-dependency, non-sequential ID, and replan limit tests).
- [tests/test_geographic_and_hotel_hardening.py](file:///c:/Users/BIT/Downloads/Travel_Agent/travel-ai/tests/test_geographic_and_hotel_hardening.py): 7/7 tests passing (geocoding disambiguation, route rejection, hotel room guidance, weather integrity).

---

## 5. Remaining Limitations and Observations

1. **Free Tier WeatherAPI Constraints**: WeatherAPI.com free tier does not provide long-range historical climate archives or forecasts beyond 14 days. The system transparently flags this limitation rather than synthesizing fake temperatures.
2. **Geoapify Places API Scope**: Geoapify provides point-of-interest metadata rather than live GDS room inventory. Live room pricing requires integration with a dedicated accommodation provider (e.g., Booking.com / Expedia API).
3. **Groq Daily Token Caps on Free Tier**: `openai/gpt-oss-120b` has a 200,000 tokens/day cap on Groq's on-demand tier. With the hardened fallback architecture, the system automatically routes to `openai/gpt-oss-20b` or `qwen/qwen3.8-27b` without interruption.
