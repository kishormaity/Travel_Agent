"""
Remote Hosted MCP Client Manager.
Uses MultiServerMCPClient from langchain-mcp-adapters to connect to remote hosted
MCP servers (MAQAMI Travel and TicketLens Experiences) using Streamable HTTP.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from loguru import logger
from langchain_core.tools import BaseTool

from app.core.config import settings
from app.mcp.remote.permissions import (
    is_remote_tool_permitted,
    requires_human_confirmation,
    REMOTE_AGENT_TOOL_PERMISSIONS,
)


class RemoteMCPClientManager:
    """
    Centralized manager for third-party hosted remote MCP servers.
    Handles startup discovery, tool caching, permission enforcement, and security guardrails.
    """

    _instance: Optional["RemoteMCPClientManager"] = None

    def __new__(cls) -> "RemoteMCPClientManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self) -> None:
        self._client: Any = None
        self._tools_cache: Dict[str, BaseTool] = {}
        self._initialized: bool = False
        self._provider_status: Dict[str, Dict[str, Any]] = {
            "maqami": {"status": "uninitialized", "url": settings.maqami_mcp_url, "tools_count": 0},
            "ticketlens": {"status": "uninitialized", "url": settings.ticketlens_mcp_url, "tools_count": 0},
            "fli": {"status": "uninitialized", "url": settings.fli_mcp_url, "tools_count": 0},
            "flight_octotrip": {"status": "uninitialized", "url": settings.octotrip_mcp_url, "tools_count": 0},
            "obo": {"status": "uninitialized", "url": settings.obo_mcp_url, "tools_count": 0},
            "hasdata": {"status": "uninitialized", "url": settings.hasdata_mcp_url, "tools_count": 0},
            "apify": {"status": "uninitialized", "url": settings.apify_mcp_url, "tools_count": 0},
        }

    def _build_client(self):
        """Build MultiServerMCPClient configured with remote connections."""
        if not settings.remote_mcp_enabled:
            logger.info("Remote MCP integration is disabled via REMOTE_MCP_ENABLED=false")
            return None

        from langchain_mcp_adapters.client import MultiServerMCPClient

        connections: Dict[str, Any] = {}

        # 1. MAQAMI Travel Connection
        if settings.maqami_mcp_url:
            headers = {"Accept": "application/json, text/event-stream"}
            if settings.maqami_mcp_api_key:
                headers["Authorization"] = f"Bearer {settings.maqami_mcp_api_key}"
            connections["maqami"] = {
                "transport": "streamable_http",
                "url": settings.maqami_mcp_url,
                "headers": headers,
                "timeout": settings.remote_mcp_timeout,
            }

        # 2. TicketLens Experiences Connection
        if settings.ticketlens_mcp_url:
            headers = {"Accept": "application/json, text/event-stream"}
            if settings.ticketlens_mcp_api_key:
                headers["Authorization"] = f"Bearer {settings.ticketlens_mcp_api_key}"
            connections["ticketlens"] = {
                "transport": "streamable_http",
                "url": settings.ticketlens_mcp_url,
                "headers": headers,
                "timeout": settings.remote_mcp_timeout,
            }

        # =====================================================================
        # FLIGHT MCP PROVIDER (OctoTrip as sole flight MCP provider)
        # =====================================================================
        if settings.fli_mcp_url:
            connections["fli"] = {
                "transport": "streamable_http",
                "url": settings.fli_mcp_url,
                "headers": {
                    "Accept": "application/json, text/event-stream",
                },
                "timeout": settings.remote_mcp_timeout,
            }

        if settings.octotrip_mcp_url:
            connections["flight_octotrip"] = {
                "transport": "streamable_http",
                "url": settings.octotrip_mcp_url,
                "headers": {
                    "Accept": "application/json, text/event-stream",
                    "User-Agent": "Claude/0.7.0",
                },
                "timeout": settings.remote_mcp_timeout,
            }

        # =====================================================================
        # ACCOMMODATION MCP PROVIDER (OBO Travel as sole accommodation MCP provider)
        # =====================================================================
        if settings.obo_mcp_url:
            obo_headers = {
                "Accept": "application/json, text/event-stream",
                "User-Agent": "Claude/0.7.0",
            }
            if settings.obo_api_key:
                obo_headers["X-OBO-Key"] = settings.obo_api_key
            connections["obo"] = {
                "transport": "streamable_http",
                "url": settings.obo_mcp_url,
                "headers": obo_headers,
                "timeout": settings.remote_mcp_timeout,
            }

        # =====================================================================
        # HASDATA MCP PROVIDER (Google Hotels, Google Maps, Google Flights)
        # =====================================================================
        if settings.hasdata_mcp_url:
            hasdata_headers = {
                "Accept": "application/json, text/event-stream",
                "User-Agent": "Claude/0.7.0",
            }
            if settings.hasdata_api_key:
                hasdata_headers["x-api-key"] = settings.hasdata_api_key
            connections["hasdata"] = {
                "transport": "streamable_http",
                "url": settings.hasdata_mcp_url,
                "headers": hasdata_headers,
                "timeout": settings.remote_mcp_timeout,
            }

        # =====================================================================
        # APIFY MCP PROVIDER (City Tourism Attractions Finder - Primary)
        # =====================================================================
        if settings.apify_mcp_url:
            apify_headers = {
                "Accept": "application/json, text/event-stream",
                "User-Agent": "Claude/0.7.0",
            }
            if settings.clean_apify_token:
                apify_headers["Authorization"] = f"Bearer {settings.clean_apify_token}"
            connections["apify"] = {
                "transport": "streamable_http",
                "url": settings.apify_mcp_url,
                "headers": apify_headers,
                "timeout": 20.0,
            }

        logger.info(f"Configuring MultiServerMCPClient with servers: {list(connections.keys())}")
        return MultiServerMCPClient(connections, tool_name_prefix=True)

    async def initialize(self) -> None:
        """
        Discover tools from remote MCP servers at application startup.
        Caches discovered tools to prevent discovery on every request.
        """
        if self._initialized:
            return

        try:
            self._client = self._build_client()
            if self._client is None:
                self._initialized = True
                return

            logger.info("Discovering tools from remote hosted MCP servers (Fli, OctoTrip, MAQAMI, TicketLens, OBO, HasData)...")
            self._tools_cache = {}

            # Discover per-server so one unavailable provider (e.g. offline local Fli) does not fail the others
            for server_name, conn in self._client.connections.items():
                try:
                    server_tools = await asyncio.wait_for(
                        self._client.get_tools(server_name=server_name),
                        timeout=12.0,
                    )
                    for t in server_tools:
                        self._tools_cache[t.name] = t
                    self._provider_status[server_name] = {
                        "status": "connected" if server_tools else "degraded",
                        "url": conn.get("url", ""),
                        "tools_count": len(server_tools),
                    }
                except Exception as se:
                    err_msg = str(se).strip() or type(se).__name__
                    logger.warning(f"Could not connect to MCP provider '{server_name}': {err_msg}")
                    self._provider_status[server_name] = {
                        "status": f"offline: {err_msg}",
                        "url": conn.get("url", ""),
                        "tools_count": 0,
                    }

            self._initialized = True
            fli_cnt = self._provider_status.get("fli", {}).get("tools_count", 0)
            octo_cnt = self._provider_status.get("flight_octotrip", {}).get("tools_count", 0)
            maqami_cnt = self._provider_status.get("maqami", {}).get("tools_count", 0)
            ticket_cnt = self._provider_status.get("ticketlens", {}).get("tools_count", 0)
            obo_cnt = self._provider_status.get("obo", {}).get("tools_count", 0)
            logger.info(
                f"Remote MCP discovery completed: {len(self._tools_cache)} tools cached "
                f"(Fli: {fli_cnt}, Flight OctoTrip: {octo_cnt}, MAQAMI: {maqami_cnt}, "
                f"TicketLens: {ticket_cnt}, OBO: {obo_cnt})"
            )
        except Exception as e:
            logger.warning(
                f"Could not initialize remote hosted MCP providers ({e}). "
                "Operating with local travel services and tools."
            )
            self._initialized = True

    def ensure_initialized(self) -> None:
        """Synchronously ensures that remote tools discovery has occurred."""
        if self._initialized:
            return
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(asyncio.run, self.initialize()).result()
            else:
                asyncio.run(self.initialize())
        except Exception as e:
            logger.warning(f"Could not complete ensure_initialized: {e}")

    def get_tools_for_agent(self, agent_name: str) -> List[BaseTool]:
        """Returns the subset of cached remote MCP tools permitted for a specific agent."""
        if not self._initialized:
            self.ensure_initialized()
        if not self._tools_cache:
            return []

        permitted_tools = []
        for tool_name, tool_obj in self._tools_cache.items():
            if is_remote_tool_permitted(agent_name, tool_name):
                permitted_tools.append(tool_obj)
        return permitted_tools

    async def aexecute_tool(
        self,
        agent_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        user_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """
        Asynchronously invoke a remote MCP tool with security guardrails:
        1. Agent permission verification
        2. Human-in-the-loop verification for irreversible operations
        3. Exception and timeout handling
        """
        # 1. Security: Permission check
        if not is_remote_tool_permitted(agent_name, tool_name):
            err_msg = f"Security Violation: Agent '{agent_name}' is not authorized to call '{tool_name}'"
            logger.warning(err_msg)
            return {"success": False, "error": err_msg, "security_violation": True}

        # 2. Security: Human-in-the-loop confirmation check
        if requires_human_confirmation(tool_name) and not user_confirmed:
            warning_msg = (
                f"Confirmation Required: Tool '{tool_name}' performs an irreversible action "
                "(booking, payment, or cancellation). Explicit user confirmation is required before proceeding."
            )
            logger.info(f"[{agent_name}] Blocked unconfirmed execution of sensitive tool '{tool_name}'")
            return {
                "success": False,
                "requires_confirmation": True,
                "error": warning_msg,
                "tool_name": tool_name,
                "arguments": arguments,
            }

        # 3. Lookup tool
        tool = self._tools_cache.get(tool_name)
        if not tool:
            # Handle potential double prefix from server-side tool names (e.g. hasdata_hasdata_*)
            if f"hasdata_{tool_name}" in self._tools_cache:
                tool = self._tools_cache[f"hasdata_{tool_name}"]
                tool_name = f"hasdata_{tool_name}"
            elif tool_name.startswith("hasdata_hasdata_") and tool_name[8:] in self._tools_cache:
                tool = self._tools_cache[tool_name[8:]]
                tool_name = tool_name[8:]
            elif "apify" in tool_name.lower() or "happitap" in tool_name.lower():
                # Flexible lookup for apify city tourism attraction tools
                for cached_name, cached_tool in self._tools_cache.items():
                    if "attraction" in cached_name.lower() or "happitap" in cached_name.lower():
                        tool = cached_tool
                        tool_name = cached_name
                        break

        if not tool:
            err_msg = f"Remote MCP tool '{tool_name}' not available or provider offline"
            logger.warning(err_msg)
            return {"success": False, "error": err_msg}

        # 4. Invoke tool
        logger.info(f"[{agent_name}] Calling remote MCP tool '{tool_name}'")
        t0 = time.time()
        try:
            # LangChain BaseTool ainvoke
            result = await tool.ainvoke(arguments)
            duration_ms = (time.time() - t0) * 1000.0
            logger.info(f"[{agent_name}] Remote MCP tool '{tool_name}' completed in {duration_ms:.2f}ms")
            return {"success": True, "data": result, "execution_duration_ms": duration_ms}
        except Exception as e:
            duration_ms = (time.time() - t0) * 1000.0
            logger.error(f"[{agent_name}] Remote MCP tool '{tool_name}' execution error after {duration_ms:.2f}ms: {e}")
            return {"success": False, "error": str(e), "execution_duration_ms": duration_ms}

    def execute_tool(
        self,
        agent_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        user_confirmed: bool = False,
    ) -> Dict[str, Any]:
        """Synchronous wrapper for tool execution."""
        if not self._initialized:
            self.ensure_initialized()
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.aexecute_tool(agent_name, tool_name, arguments, user_confirmed),
                    )
                    return future.result(timeout=settings.remote_mcp_timeout + 2.0)
            else:
                return asyncio.run(self.aexecute_tool(agent_name, tool_name, arguments, user_confirmed))
        except Exception as e:
            logger.error(f"Error in sync execute_tool for '{tool_name}': {e}")
            return {"success": False, "error": str(e)}

    def check_health(self) -> Dict[str, Any]:
        """Health status check of remote hosted MCP providers."""
        return {
            "enabled": settings.remote_mcp_enabled,
            "initialized": self._initialized,
            "total_remote_tools": len(self._tools_cache),
            "providers": self._provider_status,
        }

    async def close(self) -> None:
        """Teardown sessions cleanly."""
        self._tools_cache.clear()
        self._client = None
        self._initialized = False


# Centralized singleton instance
remote_mcp_manager = RemoteMCPClientManager()
