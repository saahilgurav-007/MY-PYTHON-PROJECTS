"""Weather API integration using Open-Meteo (zero API key required)."""

import json
import urllib.parse
import urllib.request
from typing import Dict, Any, Optional

WMO_CODE_MAP = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫️",
    48: "Depositing rime fog 🌫️",
    51: "Light drizzle 🌦️",
    53: "Moderate drizzle 🌧️",
    55: "Dense drizzle 🌧️",
    61: "Slight rain 🌦️",
    63: "Moderate rain 🌧️",
    65: "Heavy rain ⛈️",
    71: "Slight snowfall 🌨️",
    73: "Moderate snowfall 🌨️",
    75: "Heavy snowfall ❄️",
    80: "Rain showers 🌧️",
    81: "Moderate rain showers 🌧️",
    82: "Violent rain showers ⛈️",
    95: "Thunderstorm 🌩️",
    96: "Thunderstorm with slight hail ⛈️",
    99: "Thunderstorm with heavy hail ⛈️"
}

class WeatherAPI:
    """Queries live weather forecasts and conditions without requiring an API key."""

    @staticmethod
    def get_weather(location_name: str) -> Dict[str, Any]:
        """Fetches current weather for a city or region."""
        city = location_name.strip()
        if not city:
            city = "Delhi"

        try:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1&language=en&format=json"
            req = urllib.request.Request(geo_url, headers={"User-Agent": "SmartDesktopAssistant/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                geo_data = json.loads(response.read().decode("utf-8"))

            results = geo_data.get("results")
            if not results:
                return {"success": False, "message": f"Could not find coordinates for '{city}'."}

            loc = results[0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            resolved_name = f"{loc.get('name')}, {loc.get('country', '')}"

            # 2. Weather query
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            )
            w_req = urllib.request.Request(weather_url, headers={"User-Agent": "SmartDesktopAssistant/1.0"})
            with urllib.request.urlopen(w_req, timeout=5) as w_resp:
                w_data = json.loads(w_resp.read().decode("utf-8"))

            current = w_data.get("current", {})
            code = current.get("weather_code", 0)
            condition = WMO_CODE_MAP.get(code, "Clear")

            return {
                "success": True,
                "city": resolved_name,
                "temperature_c": current.get("temperature_2m"),
                "condition": condition,
                "humidity_pct": current.get("relative_humidity_2m"),
                "wind_speed_kmh": current.get("wind_speed_10m"),
                "message": (
                    f"Weather in {resolved_name}: {current.get('temperature_2m')}°C, "
                    f"{condition} (Humidity: {current.get('relative_humidity_2m')}%, Wind: {current.get('wind_speed_10m')} km/h)"
                )
            }
        except Exception as e:
            return {
                "success": False,
                "city": city,
                "message": f"Weather API error: {str(e)}"
            }
