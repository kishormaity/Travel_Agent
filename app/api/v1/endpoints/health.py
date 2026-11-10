from fastapi import APIRouter
from app.mcp.remote import remote_mcp_manager

router = APIRouter(tags=["Health"])


@router.api_route("/health", methods=["GET", "HEAD"])
def get_health():
    """Basic liveness probe."""
    return {"status": "healthy", "service": "wayfarer-travel-ai"}


@router.api_route("/ready", methods=["GET", "HEAD"])
async def get_readiness():
    """Readiness probe checking Remote MCP status."""
    checks = {}
    try:
        checks["remote_mcp_servers"] = remote_mcp_manager.check_health()
    except Exception as e:
        checks["remote_mcp_servers"] = {"status": "error", "message": str(e)}

    return {
        "status": "ready",
        "checks": checks,
    }

