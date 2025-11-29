import urllib.request


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
        wttr_url = f'https://wttr.in/{url_encoded_city}?format=%C+%t'
        response = urllib.request.urlopen(wttr_url).read()
        return response.decode('utf-8')
    except Exception as e:
        return f"Error fetching weather data"
