import urllib.request
import urllib.parse
import json


def get_weather(city: str) -> str:
    """
    Get the current weather for a given city using Open-Meteo
    Args:
      city (str): The name of the city
    Returns:
      str: The current weather condition and temperature, e.g. "Partly cloudy, 15°C"
    """
    WMO_DESCRIPTIONS = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }
    try:
        # Step 1: Geocode city → lat/lon
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode(
                {"name": city, "count": 1, "language": "en", "format": "json"}
            )
        )
        with urllib.request.urlopen(geo_url, timeout=10) as geo_resp:
            geo_data = json.loads(geo_resp.read().decode("utf-8"))
        if not geo_data.get("results"):
            return f"City '{city}' not found"
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # Step 2: Fetch current weather
        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            + urllib.parse.urlencode(
                {
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": "true",
                    "temperature_unit": "celsius",
                }
            )
        )
        weather_data = json.loads(urllib.request.urlopen(weather_url).read())
        current = weather_data["current_weather"]
        temp = current["temperature"]
        code = current["weathercode"]
        condition = WMO_DESCRIPTIONS.get(code, f"Unknown (code {code})")
        return f"{condition}, {temp}°C"
    except Exception:
        return "Error fetching weather data"


def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current time in a given timezone.
    If the user has mentioned their city, region, or timezone, pass it here.
    Defaults to UTC when no timezone is known.
    Args:
      timezone (str): A timezone name (e.g. "America/New_York", "Europe/London",
                      "Asia/Tokyo") or a UTC offset string (e.g. "UTC+2", "UTC-5").
                      Defaults to "UTC".
    Returns:
      str: The current time in the requested timezone, for example,
           "2024-01-01 12:00:00 EST (UTC-5)"
    """
    from datetime import datetime
    import zoneinfo

    try:
        tz = zoneinfo.ZoneInfo(timezone)
        now = datetime.now(tz)
        offset = now.strftime("%z")
        offset_str = f"UTC{offset[:3]}:{offset[3:]}" if offset else "UTC"
        abbrev = now.strftime("%Z")
        return now.strftime(f"%Y-%m-%d %H:%M:%S {abbrev} ({offset_str})")
    except zoneinfo.ZoneInfoNotFoundError:
        from datetime import timezone as _tz

        now_utc = datetime.now(_tz.utc)
        return (
            now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
            + f" (unknown timezone '{timezone}' — showing UTC)"
        )
