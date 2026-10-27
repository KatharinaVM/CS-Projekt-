from datetime import datetime, timezone, timedelta
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

    try:
        responses = openmeteo.weather_api(url, params=params)
    
    except Exception as error:
        print("Error while fetching weather data:", error)
        raise RuntimeError(
            "Weather data could not be retrieved. Please try again later."
        ) from error
    response = responses[0]
    daily = response.Daily()

    forecast = []

    for i in range(len(daily.Variables(0).ValuesAsNumpy())):
        forecast.append({
            "date": (
    datetime.fromtimestamp(
        daily.Time() + i * daily.Interval(),
        tz=timezone.utc
    ) + timedelta(seconds=response.UtcOffsetSeconds())
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

# Check weather for a selected hiking date
def check_weather_for_date(
    forecast,
    selected_date,
    max_rain,
    min_temperature,
    max_temperature
):
    for day in forecast:

        # Find the selected date
        if day["date"] == str(selected_date):

            # Check weather conditions
            return check_weather(
                day,
                max_rain,
                min_temperature,
                max_temperature
            )

    # Return False if the date is not in the forecast
    return False

# Get weather forecasts for multiple hiking locations
def get_weather_forecasts_batch(hikes):

    url = "https://api.open-meteo.com/v1/forecast"

    # Collect coordinates of all hikes
    latitudes = [hike["latitude"] for hike in hikes]
    longitudes = [hike["longitude"] for hike in hikes]

    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "daily": [
            "rain_sum",
            "temperature_2m_max",
            "temperature_2m_min"
        ],
        "forecast_days": 7,
        "timezone": "Europe/Zurich"
    }

    # Request weather data for all locations at once
    responses = openmeteo.weather_api(url, params=params)

    all_forecasts = []

    # Process each location separately
    for response in responses:

        daily = response.Daily()
        forecast = []

        for i in range(len(daily.Variables(0).ValuesAsNumpy())):

            forecast.append({
                "date": (
                datetime.fromtimestamp(
                    daily.Time() + i * daily.Interval(),
                    tz=timezone.utc
                ) + timedelta(seconds=response.UtcOffsetSeconds())
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

        all_forecasts.append(forecast)

    return all_forecasts

# Filter hikes based on weather conditions using batch requests
def filter_hikes_by_weather(
    hikes,
    selected_date,
    max_rain,
    min_temperature,
    max_temperature
):

    suitable_hikes = []

    # Skip hikes without coordinates
    valid_hikes = [
        hike for hike in hikes
        if hike.get("latitude") is not None
        and hike.get("longitude") is not None
    ]

    # Process hikes in batches of 20
    batch_size = 20

    for start_index in range(0, len(valid_hikes), batch_size):

        batch = valid_hikes[start_index:start_index + batch_size]

        # Get weather forecasts for the entire batch
        all_forecasts = get_weather_forecasts_batch(batch)

        # Check weather for each hike
        for hike, forecast in zip(batch, all_forecasts):

            suitable = check_weather_for_date(
                forecast,
                selected_date,
                max_rain,
                min_temperature,
                max_temperature
            )

            if suitable:
                suitable_hikes.append(hike)

    return suitable_hikes

# Test batch weather requests
if __name__ == "__main__":

    import json

    with open("hikes_data.json", "r", encoding="utf-8") as file:
        hikes = json.load(file)

    # Test with 20 hikes
    test_hikes = hikes[:20]

    suitable_hikes = filter_hikes_by_weather(
        hikes=test_hikes,
        selected_date="2026-10-29",
        max_rain=2,
        min_temperature=5,
        max_temperature=25
    )

    print("Number of tested hikes:", len(test_hikes))
    print("Number of suitable hikes:", len(suitable_hikes))

    for hike in suitable_hikes:
        print(hike["name"])
