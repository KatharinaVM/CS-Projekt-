#weather API import
import openmeteo_requests
import numpy as np
import pandas as pd
import requests_cache
from retry_requests import retry
import datetime
pd.set_option("display.max_rows", None)
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 52.52,
	"longitude": 13.41,
	"daily": ["rain_sum", "weather_code", "temperature_2m_max", "temperature_2m_min"],
	"hourly": ["temperature_2m", "precipitation_probability", "precipitation"],
	"timezone": "auto",
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = np.round(hourly.Variables(0).ValuesAsNumpy(),1)
hourly_precipitation_probability = np.round(hourly.Variables(1).ValuesAsNumpy(),1)
hourly_precipitation = np.round(hourly.Variables(2).ValuesAsNumpy(),1)

hourly_data = {
	"date": pd.date_range(
		start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = hourly.Interval()),
		inclusive = "left"
	).tz_convert(response.Timezone().decode())
}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["precipitation"] = hourly_precipitation

hourly_dataframe = pd.DataFrame(data = hourly_data)
print("\nHourly data\n", hourly_dataframe.to_string())
 
# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_rain_sum = daily.Variables(0).ValuesAsNumpy()
daily_weather_code = daily.Variables(1).ValuesAsNumpy()
daily_temperature_2m_max = np.round(daily.Variables(2).ValuesAsNumpy(),1)
daily_temperature_2m_min = np.round(daily.Variables(3).ValuesAsNumpy(),1)

daily_data = {
	"date": pd.date_range(
		start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
		end =  pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
		freq = pd.Timedelta(seconds = daily.Interval()),
		inclusive = "left"
	).tz_convert(response.Timezone().decode())
}

daily_data["Rain Volume"] = daily_rain_sum
daily_data["weather_code"] = daily_weather_code
daily_data["Temperature Low"] = daily_temperature_2m_min
daily_data["Temperature High"] = daily_temperature_2m_max

daily_dataframe = pd.DataFrame(data = daily_data)
print("\nDaily data\n", daily_dataframe)
