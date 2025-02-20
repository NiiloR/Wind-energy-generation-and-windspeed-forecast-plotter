"""
This is small program for exercise 8 on Tampere University course 
COMP.SE.221-2024-2025-1 Sustainable software engineering. The program 
fetches next 24h wind speed forecast data from open-meteo API and combines 
it into a chart with wind power generation forecast data from Fingrid 
API for the same period. To run the program, add you own fingrid 
API-key to the line 94.

Made by: Niilo Rannikko
Email: niilo.rannikko@tuni.fi
"""

import openmeteo_requests
import urllib.request, json
import urllib.parse
import requests_cache
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from retry_requests import retry
from matplotlib.dates import DateFormatter

# Function to get the latest quarter hour
def get_latest_quarter_hour():
    now = datetime.datetime.now(datetime.timezone.utc)
    # Round down to the nearest quarter hour
    new_minute = (now.minute // 15) * 15
    latest_quarter_hour = now.replace(minute=new_minute, second=0, microsecond=0)
    return latest_quarter_hour

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

start_time = get_latest_quarter_hour()
end_time = start_time + datetime.timedelta(days = 1)

# Format the start and end times
start_str = start_time.strftime('%Y-%m-%dT%H:%M')
end_str = end_time.strftime('%Y-%m-%dT%H:%M')

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 61.4991,
	"longitude": 23.7871,
	"minutely_15": "wind_speed_10m",
    "start_minutely_15": start_str,
    "end_minutely_15": end_str
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process minutely_15 data. The order of variables needs to be the same as requested.
minutely_15 = response.Minutely15()
minutely_15_wind_speed_10m = minutely_15.Variables(0).ValuesAsNumpy()

minutely_15_data = {"date": pd.date_range(
	start = pd.to_datetime(minutely_15.Time(), unit = "s", utc = True),
	end = pd.to_datetime(minutely_15.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = minutely_15.Interval()),
	inclusive = "left"
)}

minutely_15_data["wind_speed_10m"] = minutely_15_wind_speed_10m

minutely_15_dataframe = pd.DataFrame(data = minutely_15_data)
print(minutely_15_dataframe)


findridAPI_KEY = FINGRID_API_KEY
datasetId = "245"
start = get_latest_quarter_hour()
end = start + datetime.timedelta(days=1)
print(start, end)

start_str = start.isoformat(timespec='seconds') + 'Z'
end_str = end.isoformat(timespec='seconds') + 'Z'

try:

    url2 = "https://data.fingrid.fi/api/datasets/245/data?startTime=2025-02-20T18:45:00Z&endTime=2025-02-21T18:45:00Z&format=json&pageSize=1000"
    hdr ={
    # Request headers
    'Cache-Control': 'no-cache',
    'x-api-key': 'e4df54200c974ecc85e9f35485933861'  # Add your API key here
    }

    req = urllib.request.Request(url2, headers=hdr)

    req.get_method = lambda: 'GET'
    response = urllib.request.urlopen(req)
    data = json.loads(response.read())

    # Extract values and save them to a list
    values_list = [entry['value'] for entry in data['data']]

    # Plotting
    fig, ax1 = plt.subplots()

    # Plot wind speed from DataFrame on primary y-axis
    ax1.plot(minutely_15_dataframe['date'], minutely_15_dataframe['wind_speed_10m'], label='Wind Speed in Tampere', color='blue')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Wind Speed Forecast', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Create secondary y-axis
    ax2 = ax1.twinx()
    values_dates = pd.date_range(start=start, periods=len(values_list), freq='15min')
    ax2.plot(values_dates, values_list, label='Wind power generation forecast', color='orange')
    ax2.set_ylabel('Wind Power Generation Forecast', color='orange')
    ax2.tick_params(axis='y', labelcolor='orange')

    # Customize x-axis to show only hour and minutes
    date_format = DateFormatter('%H:%M')
    ax1.xaxis.set_major_formatter(date_format)
    fig.autofmt_xdate()

    # Customize plot
    fig.suptitle('Wind Speed and Wind Power Generation Forecast Comparison for the next 24h')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    plt.show()
except Exception as e:
    print("Virhe: ", e)
    