from datetime import datetime, timezone, timedelta

import openmeteo_requests
import requests_cache
from retry_requests import retry


# --------------------------------------------------
# 1. Open-Meteo-Verbindung
# --------------------------------------------------

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


# --------------------------------------------------
# 2. Wetterdaten für einen Standort abrufen
# --------------------------------------------------

def get_weather_forecast(latitude, longitude):

    forecasts = get_weather_forecasts_batch([
        {
            "latitude": latitude,
            "longitude": longitude
        }
    ])

    return forecasts[0]


# --------------------------------------------------
# 3. Wetterdaten für mehrere Standorte abrufen
# --------------------------------------------------

def get_weather_forecasts_batch(hikes):

    if not hikes:
        return []

    url = "https://api.open-meteo.com/v1/forecast"

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

    try:
        responses = openmeteo.weather_api(
            url,
            params=params
        )

    except Exception as error:
        raise RuntimeError(
            "Weather data could not be retrieved. "
            "Please try again later."
        ) from error

    all_forecasts = []

    for response in responses:

        daily = response.Daily()

        rain_values = daily.Variables(0).ValuesAsNumpy()
        max_values = daily.Variables(1).ValuesAsNumpy()
        min_values = daily.Variables(2).ValuesAsNumpy()

        forecast = []

        for i in range(len(rain_values)):

            forecast_date = (
                datetime.fromtimestamp(
                    daily.Time() + i * daily.Interval(),
                    tz=timezone.utc
                )
                + timedelta(
                    seconds=response.UtcOffsetSeconds()
                )
            ).strftime("%Y-%m-%d")

            forecast.append({
                "date": forecast_date,
                "rain_mm": float(rain_values[i]),
                "temperature_max": float(max_values[i]),
                "temperature_min": float(min_values[i])
            })

        all_forecasts.append(forecast)

    return all_forecasts


# --------------------------------------------------
# 4. Wetterbedingungen überprüfen
# --------------------------------------------------

def check_weather(
    day,
    max_rain,
    min_temperature,
    max_temperature
):

    if day["rain_mm"] > max_rain:
        return False

    if day["temperature_min"] < min_temperature:
        return False

    if day["temperature_max"] > max_temperature:
        return False

    return True


# --------------------------------------------------
# 5. Wetter für ein bestimmtes Datum überprüfen
# --------------------------------------------------

def check_weather_for_date(
    forecast,
    selected_date,
    max_rain,
    min_temperature,
    max_temperature
):

    for day in forecast:

        if day["date"] == str(selected_date):

            return check_weather(
                day,
                max_rain,
                min_temperature,
                max_temperature
            )

    return False


# --------------------------------------------------
# 6. Wanderungen nach Wetter filtern
# --------------------------------------------------

def filter_hikes_by_weather(
    hikes,
    selected_date,
    max_rain,
    min_temperature,
    max_temperature
):

    suitable_hikes = []

    valid_hikes = [
        hike for hike in hikes
        if hike.get("latitude") is not None
        and hike.get("longitude") is not None
    ]

    batch_size = 20

    for start_index in range(
        0,
        len(valid_hikes),
        batch_size
    ):

        batch = valid_hikes[
            start_index:start_index + batch_size
        ]

        all_forecasts = get_weather_forecasts_batch(
            batch
        )

        for hike, forecast in zip(
            batch,
            all_forecasts
        ):

            matching_day = next(
                (
                    day for day in forecast
                    if day["date"] == str(selected_date)
                ),
                None
            )

            if matching_day is None:
                continue

            suitable = check_weather(
                matching_day,
                max_rain,
                min_temperature,
                max_temperature
            )

            if suitable:

                # Wetterdaten zusätzlich speichern
                hike_with_weather = hike.copy()

                hike_with_weather["weather"] = matching_day

                suitable_hikes.append(
                    hike_with_weather
                )

    return suitable_hikes


# --------------------------------------------------
# 7. Test
# --------------------------------------------------

if __name__ == "__main__":

    import json
    from pathlib import Path

    data_path = Path(__file__).resolve().parent / "hikes_data.json"

    with data_path.open("r", encoding="utf-8") as file:
        hikes = json.load(file)

    test_hikes = hikes[:40]

    suitable_hikes = filter_hikes_by_weather(
        hikes=test_hikes,
        selected_date=datetime.now().date(),
        max_rain=2,
        min_temperature=5,
        max_temperature=25
    )

    print("Number of tested hikes:", len(test_hikes))
    print("Number of suitable hikes:", len(suitable_hikes))

    for hike in suitable_hikes:

        print("---------------------------")
        print("Hike:", hike.get("name"))

        weather = hike["weather"]

        print("Date:", weather["date"])
        print("Rain:", weather["rain_mm"], "mm")
        print(
            "Minimum temperature:",
            weather["temperature_min"],
            "°C"
        )
        print(
            "Maximum temperature:",
            weather["temperature_max"],
            "°C"
        )
