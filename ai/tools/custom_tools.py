import urllib.request
import urllib.parse
import json


def get_weather(city: str) -> str:
    """
    Get the current weather for a given city using Open-Meteo
    Args:
      city (str): The name of the city
    Returns:
      str: The current weather, for example "WMO code 3, 15°C" (WMO code representing weather conditions)
    """
    try:
        # Step 1: Geocode city → lat/lon
        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            + urllib.parse.urlencode({"name": city, "count": 1, "language": "en", "format": "json"})
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
            + urllib.parse.urlencode({
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "temperature_unit": "celsius",
            })
        )
        weather_data = json.loads(urllib.request.urlopen(weather_url).read())
        current = weather_data["current_weather"]
        temp = current["temperature"]
        code = current["weathercode"]
        return f"WMO code {code}, {temp}°C"
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
