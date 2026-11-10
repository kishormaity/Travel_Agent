import os
import uvicorn
from fli.mcp.server import mcp

app = mcp.http_app()

@app.get("/health")
def health():
    return {"status": "ok", "service": "fli_google_flights"}

def run_server(host: str | None = None, port: int | None = None) -> None:
    server_host = host or os.getenv("FLI_HOST", "127.0.0.1")
    server_port = port or int(os.getenv("FLI_PORT", "8001"))
    print(f"Starting Fli Google Flights MCP Server on http://{server_host}:{server_port}/mcp/ ...")
    uvicorn.run(app, host=server_host, port=server_port, log_level="info")

if __name__ == "__main__":
    run_server()
