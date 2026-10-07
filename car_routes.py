import os
import openrouteservice
from dotenv import load_dotenv

load_dotenv(".env.jonathan")

api_key = os.getenv("ORS_API_KEY")

client = openrouteservice.Client(key=api_key)

# function to get out route

def get_car_route(start_coordinates, destination_coordinates):

    coordinates = [
        start_coordinates,
        destination_coordinates
    ]

    route = client.directions(
        coordinates=coordinates,
        profile="driving-car",
        format="geojson"
    )

    distance = route["features"][0]["properties"]["segments"][0]["distance"]
    duration = route["features"][0]["properties"]["segments"][0]["duration"]

    distance_km = distance / 1000
    duration_minutes = duration / 60

    return distance_km, duration_minutes

# function to get the coordinates from our input location

def get_coordinates(place):

    result = client.pelias_search(
        text = place,
        country = "CH",
        layers = ["locality"]
    )

    coordinates = result["features"][0]["geometry"]["coordinates"]

    return coordinates

place = "Winterthur, Switzerland"

coordinates = get_coordinates(place)

print("Coordinates:", coordinates)

winterthur = get_coordinates("Winterthur")
st_gallen = get_coordinates("St. Gallen")

print("Winterthur:", winterthur)
print("St. Gallen:", st_gallen)

distance, duration = get_car_route(winterthur, st_gallen)

print("Driving distance:", round(distance, 1), "km")
print("Driving time:", round(duration), "minutes")

# function checks the driving time from desired location

def check_driving_time(driving_time, max_driving_time):

    if driving_time <= max_driving_time:
        return True
    else:
        return False

hikes = [
    {"name": "Säntis", "driving_time": 75},
    {"name": "Flumserberg", "driving_time": 55},
    {"name": "Lauterbrunnen", "driving_time": 140}
]

max_driving_time = 90

reachable_hikes = []

for hike in hikes:

    driving_time = hike["driving_time"]

    if check_driving_time(driving_time, max_driving_time):

        reachable_hikes.append(hike)

print(reachable_hikes)