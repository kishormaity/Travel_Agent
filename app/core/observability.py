import time
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from loguru import logger

# Keys that may contain sensitive credentials
SECRET_KEY_PATTERN = re.compile(
    r"(api[_-]?key|access[_-]?token|auth|password|secret|bearer|credential|private[_-]?key)",
    re.IGNORECASE,
)


def sanitize_secrets(obj: Any) -> Any:
    """
    Recursively sanitize dictionaries, lists, and strings to ensure no API keys,
    access tokens, or secrets are ever emitted to application logs.
    """
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            if SECRET_KEY_PATTERN.search(str(k)):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = sanitize_secrets(v)
        return sanitized
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize_secrets(item) for item in obj]
    elif isinstance(obj, str):
        # Redact bearer token patterns if embedded in strings
        if "bearer " in obj.lower():
            obj = re.sub(r"(?i)bearer\s+[A-Za-z0-9_\-\.]+", "Bearer ***REDACTED***", obj)
        return obj
    elif hasattr(obj, "model_dump"):
        return sanitize_secrets(obj.model_dump())
    return obj


def log_specialist_task_start(
    task_id: Any,
    specialist_name: str,
    selected_mcp_server: str,
    selected_tool: str,
    arguments: Dict[str, Any],
) -> float:
    """Logs start of a specialist task execution with sanitized arguments."""
    start_ts = time.time()
    sanitized_args = sanitize_secrets(arguments or {})
    start_str = datetime.utcfromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    logger.info(
        f"[SpecialistTask:START] TaskID: {task_id} | Specialist: {specialist_name} | "
        f"MCP Server: {selected_mcp_server} | Tool: {selected_tool} | "
        f"Start: {start_str} | Sanitized Args: {sanitized_args}"
    )
    return start_ts


def log_specialist_task_end(
    task_id: Any,
    specialist_name: str,
    selected_mcp_server: str,
    selected_tool: str,
    start_time: float,
    status: str,
    raw_response: Any = None,
    exception: Any = None,
) -> None:
    """Logs completion or failure of a specialist task with sanitized response/error."""
    end_ts = time.time()
    latency_ms = (end_ts - start_time) * 1000.0
    end_str = datetime.utcfromtimestamp(end_ts).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if exception is not None or status.upper() in ("FAILED", "ERROR"):
        sanitized_err = sanitize_secrets(str(exception) if exception else str(raw_response))
        logger.error(
            f"[SpecialistTask:END] TaskID: {task_id} | Specialist: {specialist_name} | "
            f"MCP Server: {selected_mcp_server} | Tool: {selected_tool} | "
            f"Status: FAILED | Latency: {latency_ms:.2f}ms | End: {end_str} | "
            f"Raw Error: {sanitized_err}"
        )
    else:
        # Comment out verbose flight data from CLI logging to keep terminal output clean
        if specialist_name == "flight_agent" or "flight" in str(selected_tool).lower():
            count = 0
            if isinstance(raw_response, dict):
                count = raw_response.get("count", len(raw_response.get("flights", [])))
            elif isinstance(raw_response, list):
                count = len(raw_response)
            logger.info(
                f"[SpecialistTask:END] TaskID: {task_id} | Specialist: {specialist_name} | "
                f"MCP Server: {selected_mcp_server} | Tool: {selected_tool} | "
                f"Status: {status.upper()} | Latency: {latency_ms:.2f}ms | End: {end_str} | "
                f"Total Offers: {count}"
                # Flight data commented out as requested:
                # f" | Raw Response: {sanitized_resp}"
            )
        else:
            sanitized_resp = sanitize_secrets(raw_response)
            logger.info(
                f"[SpecialistTask:END] TaskID: {task_id} | Specialist: {specialist_name} | "
                f"MCP Server: {selected_mcp_server} | Tool: {selected_tool} | "
                f"Status: {status.upper()} | Latency: {latency_ms:.2f}ms | End: {end_str} | "
                f"Raw Response: {sanitized_resp}"
            )
