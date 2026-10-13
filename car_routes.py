import os
import json
import math
import openrouteservice
from dotenv import load_dotenv
import requests

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

# function checks the driving time from desired location

def check_driving_time(driving_time, max_driving_time):

    if driving_time <= max_driving_time:
        return True
    else:
        return False

def get_straight_line_distance(start_coordinates, destination_coordinates):

    start_longitude, start_latitude = start_coordinates
    destination_longitude, destination_latitude = destination_coordinates

    latitude_1 = math.radians(start_latitude)
    latitude_2 = math.radians(destination_latitude)

    latitude_difference = math.radians(
        destination_latitude - start_latitude
    )

    longitude_difference = math.radians(
        destination_longitude - start_longitude
    )

    a = (
        math.sin(latitude_difference / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_difference / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    earth_radius_km = 6371

    return earth_radius_km * c


# Filter hikes based on driving time

def filter_hikes_by_car(hikes, start_location, max_driving_time):

    # Convert the user's starting location into coordinates
    start_coordinates = get_coordinates(start_location)

    # First filter hikes by straight-line distance
    nearby_hikes = []

    max_straight_line_distance = (max_driving_time / 60) * 130

    for hike in hikes:

        if hike["longitude"] is None or hike["latitude"] is None:
            continue

        hike_coordinates = [
            hike["longitude"],
            hike["latitude"]
        ]

        straight_line_distance = get_straight_line_distance(
            start_coordinates,
            hike_coordinates
        )

        if straight_line_distance <= max_straight_line_distance:
            nearby_hikes.append(hike)

    batch_size = 5

    reachable_hikes = []

    def process_batch(batch):
        print("Processing a batch of", len(batch), "hikes")

        locations = [start_coordinates]

        for hike in batch:
            locations.append([
                hike["longitude"],
                hike["latitude"]
            ])

        try:
            matrix = client.distance_matrix(
                locations=locations,
                profile="driving-car",
                sources=[0],
                destinations=list(range(1, len(locations))),
                metrics=["distance", "duration"]
            )

        except openrouteservice.exceptions.ApiError as error:

            if error.status == 403:
                raise RuntimeError(
                    "OpenRouteService returned HTTP 403. "
                    "Cannot calculate complete hiking results."
                ) from error

            print("Matrix API error:", error)

            if len(batch) == 1:
                raise RuntimeError(
                    "Could not calculate the driving time for: "
                    + batch[0]["name"]
                ) from error

            midpoint = len(batch) // 2

            process_batch(batch[:midpoint])
            process_batch(batch[midpoint:])

            return

        except (requests.exceptions.RequestException, TimeoutError) as error:
            raise RuntimeError(
                "Network error while calculating driving times. "
                "The hiking results could not be completed."
            ) from error
        
        for i, hike in enumerate(batch):

            duration_seconds = matrix["durations"][0][i]
            distance_meters = matrix["distances"][0][i]

            if duration_seconds is None or distance_meters is None:
                continue

            duration_minutes = duration_seconds / 60
            distance_km = distance_meters / 1000

            if check_driving_time(duration_minutes, max_driving_time):

                reachable_hike = hike.copy()

                reachable_hike["driving_time_min"] = round(duration_minutes)
                reachable_hike["driving_distance_km"] = round(distance_km, 1)

                reachable_hikes.append(reachable_hike)

    for start_index in range(0, len(nearby_hikes), batch_size):

        batch_number = start_index // batch_size + 1
        print("Processing batch:", batch_number)

        batch = nearby_hikes[start_index:start_index + batch_size]

        process_batch(batch)

    return reachable_hikes

# Test our reusable function

if __name__ == "__main__":

    # Load hiking data
    with open("hikes_data.json", "r", encoding="utf-8") as file:
        hikes = json.load(file)

    # Run the car accessibility filter
    reachable_hikes = filter_hikes_by_car(
        hikes,
        start_location="Winterthur",
        max_driving_time=90
    )

    print("Reachable hikes:", len(reachable_hikes))

    for hike in reachable_hikes:
        print(
            hike["name"],
            "-",
            hike["driving_time_min"],
            "minutes"
        )