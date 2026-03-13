import urllib.request
import urllib.parse


def get_weather(city: str) -> str:
    """
    Get the current weather for a given city
    Args:
      city (str): The name of the city
    Returns:
      str: The current weather in the city, for example, "Sunny +20°C"
    """
    try:
        url_encoded_city = urllib.parse.quote_plus(city)
        wttr_url = f"https://wttr.in/{url_encoded_city}?format=%C+%t"
        response = urllib.request.urlopen(wttr_url).read()
        return response.decode("utf-8")
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
