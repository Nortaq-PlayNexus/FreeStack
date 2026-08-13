"""
freestack-mcp-py — Python FastMCP server.

Deploy to FastMCP Cloud (free personal tier) with:
    pip install "fastmcp[cli]"
    fastmcp deploy server.py

Or run locally over stdio:
    fastmcp run server.py

Tools here are backed by free, keyless APIs (Open-Meteo) so this is 100% free end to end.
"""
from fastmcp import FastMCP
import json, os, urllib.request

mcp = FastMCP("freestack-mcp-py")

_NOTES: dict[str, str] = {}


@mcp.tool()
def get_weather(latitude: float, longitude: float) -> str:
    """Current weather + 1-day forecast for a latitude/longitude."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,weather_code,wind_speed_10m&forecast_days=1"
    )
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()


@mcp.tool()
def save_note(key: str, value: str) -> str:
    """Save a note in the in-memory store."""
    _NOTES[key] = value
    return f"saved note '{key}'"


@mcp.tool()
def get_note(key: str) -> str:
    """Read a note back."""
    return _NOTES.get(key, f"no note stored under '{key}'")


@mcp.tool()
def list_notes() -> str:
    """List every saved note key."""
    return json.dumps(list(_NOTES.keys()))


if __name__ == "__main__":
    # transports: "stdio" (default, for local/embedded use) or "streamable-http"
    # (FastMCP Cloud / any HTTP host). Override with MCP_TRANSPORT=streamable-http.
    mcp.run(transport=os.environ.get("MCP_TRANSPORT", "stdio"))
