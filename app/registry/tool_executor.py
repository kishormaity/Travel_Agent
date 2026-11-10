import json
from typing import Any
from loguru import logger
from app.schemas.tool_result import ToolResult

def _format_tool_response_for_cli(result: Any) -> str:
    """Format tool result into clean, structured JSON for CLI output."""
    try:
        if isinstance(result, ToolResult):
            payload = result.model_dump()
        elif hasattr(result, "model_dump"):
            payload = result.model_dump()
        elif hasattr(result, "dict"):
            payload = result.dict()
        elif isinstance(result, (dict, list)):
            payload = result
        else:
            return str(result)

        return json.dumps(payload, indent=2, default=str, ensure_ascii=False)
    except Exception:
        return str(result)


def _detect_tool_provider(tool_name: str, result: Any = None) -> str:
    """Identify the exact provider or MCP server that fulfilled the tool call."""
    if result is not None:
        if hasattr(result, "metadata") and isinstance(result.metadata, dict):
            if result.metadata.get("provider"):
                return result.metadata["provider"]
            if result.metadata.get("mcp_tool"):
                return f"Remote MCP: {result.metadata['mcp_tool']}"

        data = result.data if hasattr(result, "data") else result
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            src = data[0].get("data_source") or data[0].get("source_provider") or data[0].get("provider")
            if src == "apify_mcp":
                return "Apify MCP Server (happitap/city-tourism-attractions-finder)"
            if src == "geoapify_places":
                return "Geoapify Places API"
            if src == "hasdata_google_hotels":
                return "HasData Google Hotels MCP"
            if src == "fli_google_flights":
                return "Fli Google Flights MCP ('fli_search_flights')"
            if src == "octotrip":
                return "OctoTrip Flight MCP ('flight_octotrip')"
            if src:
                return str(src)

        if isinstance(data, dict):
            src = data.get("provider") or data.get("source_provider") or data.get("data_source")
            if src:
                return str(src)

    # Defaults by tool category
    if "place" in tool_name.lower():
        from app.core.config import settings
        if settings.apify_api_token:
            return "Apify MCP Server (happitap/city-tourism-attractions-finder) [Primary]"
        return "Apify MCP Server [Pending APIFY_TOKEN; Fallback: Geoapify Places API]"
    if "flight" in tool_name.lower():
        return "Remote MCP fli_search_flights / AviationStack API"
    if "hotel" in tool_name.lower():
        return "HasData Google Hotels MCP / Geoapify Places"
    if tool_name == "get_current_weather":
        return "Open-Meteo & WeatherAPI"
    if tool_name == "convert_currency":
        return "Frankfurter Currency API"
    if tool_name == "get_route":
        return "Geoapify Routing API"
    return tool_name


class ToolExecutor:
    """
    Executes tool calls requested by the LLM.
    """

    def execute(self, tool_name: str, arguments: dict):
        """
        Execute a tool with the provided arguments.

        Args:
            tool_name: Name of the tool selected by the LLM.
            arguments: Arguments required by the tool.

        Returns:
            Result returned by the tool.
        """
        from app.registry.tool_registry import AVAILABLE_TOOLS

        arguments = arguments or {}
        provider_hint = _detect_tool_provider(tool_name, None)
        logger.info(
            f"\n{'=' * 75}\n"
            f"🚀 [TOOL INVOCATION STARTED] -> {tool_name}\n"
            f"🔌 Provider / MCP: {provider_hint}\n"
            f"📋 Arguments: {arguments}\n"
            f"{'=' * 75}"
        )

        tool = AVAILABLE_TOOLS.get(tool_name)

        if tool is None:
            raise ValueError(
                f"Unknown tool: {tool_name}"
            )

        try:
            if hasattr(tool, "invoke"):
                result = tool.invoke(arguments)
            else:
                result = tool(**arguments)

            provider_name = _detect_tool_provider(tool_name, result)

            # Suppress flight and hotel details output in CLI as requested; all other tools continue printing full response
            suppressed_keywords = ("flight", "hotel", "accommodation")
            if not any(kw in tool_name.lower() for kw in suppressed_keywords):
                if tool_name == "search_places" or "place" in tool_name.lower():
                    # Format as clean numbered destination attraction list in CLI
                    places_list = result.data if hasattr(result, "data") else (result if isinstance(result, list) else [])
                    city_name = str(arguments.get("city", "")).strip() or "Destination"
                    from app.tools.places import format_places_cli_table
                    cli_table = format_places_cli_table(places_list, city_name, provider=provider_name)
                    logger.info(
                        f"\n{'=' * 75}\n"
                        f"📥 [TOOL INVOCATION RESPONSE] -> {tool_name}\n"
                        f"🔌 Provider / MCP Invoked: {provider_name}\n"
                        f"{'-' * 75}\n"
                        f"{cli_table}\n"
                        f"{'=' * 75}"
                    )
                else:
                    formatted_response = _format_tool_response_for_cli(result)
                    logger.info(
                        f"\n{'=' * 75}\n"
                        f"📥 [TOOL INVOCATION RESPONSE] -> {tool_name}\n"
                        f"🔌 Provider / MCP Invoked: {provider_name}\n"
                        f"{'-' * 75}\n"
                        f"{formatted_response}\n"
                        f"{'=' * 75}"
                    )
            else:
                # Flight and hotel details suppressed from CLI printing as requested; acknowledge execution & provider
                count_str = f" ({len(result.data)} results retrieved)" if hasattr(result, "data") and isinstance(result.data, list) else ""
                logger.info(
                    f"\n{'=' * 75}\n"
                    f"📥 [TOOL INVOCATION RESPONSE] -> {tool_name}{count_str}\n"
                    f"🔌 Provider / MCP Invoked: {provider_name}\n"
                    f"ℹ️  [Detailed results table suppressed in CLI as requested]\n"
                    f"{'=' * 75}"
                )

            return result

        except Exception as error:

            logger.exception(
                f"Tool execution failed: {tool_name}"
            )

            raise error