from typing import Any

import httpx
from langchain_core.tools import tool

# These are constant for this file
NWS_API_WEATHER_ALERT_URL = "https://api.weather.gov/alerts/active/area/"
USER_AGENT = "weather-app/1.0"

# This decorator (@tool) defines this function as a Langchain tool
# Its important to have a descriptive function name, descriptive inputs, and a docstring
# LLM will use these when selecting a tool
@tool
def get_us_state_weather_alerts(us_state_code: str) -> dict[str, Any] | None:
    """
    Gets weather alerts from a particular US state.
    Args:
        us_state_code (str): two-letter US state code (e.g. CA, NY) specified in query.
    Returns:
        weather alerts in specified state.
    """
    headers = {
        "User-Agent": USER_AGENT
    }
    url = NWS_API_WEATHER_ALERT_URL + us_state_code
    # Here we use httpx to make a GET request to the NWS Weather API
    # We just return this result
    # This will be the tool result
    with httpx.Client() as client:
        try:
            response = client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return None