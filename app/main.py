import sys
import os
import subprocess
import time
import requests
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# Ensure loguru prints to sys.stdout with color and instant flushing in terminal
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

from app.api.v1.router import api_v1_router
from app.api.v1.endpoints.health import router as health_router

_fli_proc: subprocess.Popen | None = None


def _ensure_fli_running():
    global _fli_proc
    health_url = os.getenv("FLI_HEALTH_URL", "http://127.0.0.1:8001/health")
    try:
        r = requests.get(health_url, timeout=1)
        if r.status_code == 200:
            logger.info("Fli Google Flights MCP server is already running on port 8001.")
            return
    except Exception:
        pass

    logger.info("Starting local Fli Google Flights MCP server on port 8001...")
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{base_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        _fli_proc = subprocess.Popen(
            [sys.executable, "-m", "app.mcp.servers.fli_server"],
            cwd=base_dir,
            env=env,
        )
        for _ in range(30):
            try:
                r = requests.get(health_url, timeout=1)
                if r.status_code == 200:
                    logger.info("Fli MCP server started successfully on http://127.0.0.1:8001/mcp/")
                    break
            except Exception:
                time.sleep(0.3)
    except Exception as e:
        logger.warning(f"Could not auto-start Fli MCP server: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Wayfarer AI Travel Agent...")
    # Ensure Fli MCP server is online before remote manager initialization
    _ensure_fli_running()

    # Initialize remote hosted MCP client and discover tools at startup
    try:
        from app.mcp.remote import remote_mcp_manager
        await remote_mcp_manager.initialize()
        logger.info("Remote MCP manager initialized successfully.")
    except Exception as e:
        logger.warning(f"Remote MCP startup initialization warning: {e}")

    logger.info("Wayfarer Travel Agent API is ready for requests at http://127.0.0.1:8000")
    try:
        yield
    finally:
        logger.info("Shutting down Wayfarer AI Travel Agent...")
        try:
            from app.mcp.remote import remote_mcp_manager
            await remote_mcp_manager.close()
            logger.info("Remote MCP connections closed.")
        except Exception as e:
            logger.warning(f"Error during remote MCP teardown: {e}")

        global _fli_proc
        if _fli_proc:
            try:
                _fli_proc.terminate()
                _fli_proc.wait(timeout=3)
                logger.info("Fli MCP server subprocess terminated.")
            except Exception:
                pass


app = FastAPI(
    title="Wayfarer AI Travel Agent API",
    description="Production-grade AI Travel Agent orchestrating LangGraph StateGraph, HasData Hotels MCP, and flight/places services.",
    version="2.1.0",
    lifespan=lifespan,
)

# CORS Configuration - allow frontend dev server and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "*",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Top-level health routes (/health, /ready)
app.include_router(health_router)

# Root status route (supports both GET and HEAD for cloud health probes)
@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "status": "online",
        "service": "Wayfarer AI Travel Agent API",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/health",
    }

# Mount API v1 Routes (/api/v1/...)
app.include_router(api_v1_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "InternalServerError", "message": str(exc)},
    )

