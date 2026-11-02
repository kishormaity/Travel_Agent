"""
Remote Hosted MCP Integration Package.
"""

from app.mcp.remote.manager import RemoteMCPClientManager, remote_mcp_manager
from app.mcp.remote.permissions import (
    REMOTE_AGENT_TOOL_PERMISSIONS,
    SENSITIVE_IRREVERSIBLE_TOOLS,
    is_remote_tool_permitted,
    requires_human_confirmation,
)

__all__ = [
    "RemoteMCPClientManager",
    "remote_mcp_manager",
    "REMOTE_AGENT_TOOL_PERMISSIONS",
    "SENSITIVE_IRREVERSIBLE_TOOLS",
    "is_remote_tool_permitted",
    "requires_human_confirmation",
]
