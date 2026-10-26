from datetime import datetime
import openmeteo_requests
import requests_cache
from retry_requests import retry


# Open-Meteo-Client mit Cache und automatischen Wiederholungen
cache_session = requests_cache.CachedSession(
    ".cache",
    expire_after=3600
)

retry_session = retry(
    cache_session,
    retries=5,
    backoff_factor=0.2
)

openmeteo = openmeteo_requests.Client(
    session=retry_session
)


# Get weather forecast for a location
def get_weather_forecast(latitude, longitude):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "rain_sum",
            "temperature_2m_max",
            "temperature_2m_min"
        ],
        "forecast_days": 7,
        "timezone": "auto"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()

    forecast = []

    for i in range(len(daily.Variables(0).ValuesAsNumpy())):
        forecast.append({
            "date": datetime.fromtimestamp(
                daily.Time() + i * daily.Interval()
            ).strftime("%Y-%m-%d"),
            "rain_mm": float(
                daily.Variables(0).ValuesAsNumpy()[i]
            ),
            "temperature_max": float(
                daily.Variables(1).ValuesAsNumpy()[i]
            ),
            "temperature_min": float(
                daily.Variables(2).ValuesAsNumpy()[i]
            )
        })

    return forecast


# Check if weather conditions match the user's preferences
def check_weather(day, max_rain, min_temperature, max_temperature):

    # Check rainfall
    if day["rain_mm"] > max_rain:
        return False

    # Check minimum temperature
    if day["temperature_min"] < min_temperature:
        return False

    # Check maximum temperature
    if day["temperature_max"] > max_temperature:
        return False

    return True


# Test the weather filter
if __name__ == "__main__":

    # Get weather forecast for Bern
    forecast = get_weather_forecast(
        latitude=46.95,
        longitude=7.45
    )

    # Print all forecast days
    for day in forecast:
        print(day)

    # Check which days have suitable weather
    print("\nDays with suitable weather:")

    for day in forecast:
        if check_weather(
            day,
            max_rain=2,
            min_temperature=5,
            max_temperature=25
        ):
            print(day["date"], "- Suitable weather")
