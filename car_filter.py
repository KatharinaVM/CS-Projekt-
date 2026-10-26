import os
import math
import json

import openrouteservice
from dotenv import load_dotenv


# --------------------------------------------------
# 1. API configuration
# --------------------------------------------------

load_dotenv(".env.jonathan")


def get_ors_client():
    """Create the OpenRouteService client."""

    api_key = os.getenv("ORS_API_KEY")

    if not api_key:
        raise RuntimeError(
            "ORS_API_KEY was not found. "
            "Please check your .env.jonathan file."
        )

    return openrouteservice.Client(key=api_key)


# --------------------------------------------------
# 2. Convert the user's starting location to coordinates
# --------------------------------------------------

def get_coordinates(place, client):
    """Return coordinates as [longitude, latitude]."""

    result = client.pelias_search(
        text=place,
        country="CH",
        layers=["locality"]
    )

    features = result.get("features", [])

    if not features:
        raise ValueError(
            f"No location found for '{place}'. "
            "Please enter a Swiss town or city."
        )

    return features[0]["geometry"]["coordinates"]


# --------------------------------------------------
# 3. Calculate straight-line distance
# --------------------------------------------------

def get_straight_line_distance(
    start_coordinates,
    destination_coordinates
):
    """Calculate the distance in kilometres."""

    start_lon, start_lat = start_coordinates
    dest_lon, dest_lat = destination_coordinates

    lat1 = math.radians(start_lat)
    lat2 = math.radians(dest_lat)

    delta_lat = math.radians(dest_lat - start_lat)
    delta_lon = math.radians(dest_lon - start_lon)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    # Protect against small floating-point rounding errors
    a = min(1.0, max(0.0, a))

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    earth_radius_km = 6371

    return earth_radius_km * c


# --------------------------------------------------
# 4. Filter hikes by maximum driving time
# --------------------------------------------------

def filter_hikes_by_car(
    hikes,
    start_location,
    max_driving_time
):
    """
    Filter hikes by maximum driving time in minutes.

    Returns a list of matching hikes. Each result includes
    driving_time_min and driving_distance_km.
    """

    if max_driving_time <= 0:
        raise ValueError(
            "Maximum driving time must be greater than zero."
        )

    client = get_ors_client()

    # Find the user's starting coordinates
    start_coordinates = get_coordinates(
        start_location,
        client
    )

    # Keep hikes with valid coordinates
    valid_hikes = []

    for hike in hikes:
        latitude = hike.get("latitude")
        longitude = hike.get("longitude")

        if latitude is None or longitude is None:
            continue

        valid_hikes.append(hike)

    # Preliminary filter to reduce API requests
    nearby_hikes = []

    max_straight_line_distance = (
        max_driving_time / 60
    ) * 130

    for hike in valid_hikes:
        hike_coordinates = [
            hike["longitude"],
            hike["latitude"]
        ]

        straight_distance = get_straight_line_distance(
            start_coordinates,
            hike_coordinates
        )

        if straight_distance <= max_straight_line_distance:
            nearby_hikes.append(hike)

    # Calculate actual driving times in small batches
    batch_size = 5
    reachable_hikes = []

    for start_index in range(
        0, len(nearby_hikes), batch_size
    ):
        batch = nearby_hikes[
            start_index:start_index + batch_size
        ]

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
                destinations=list(
                    range(1, len(locations))
                ),
                metrics=["distance", "duration"]
            )

        except openrouteservice.exceptions.ApiError as error:
            raise RuntimeError(
                "OpenRouteService could not calculate "
                "the driving times. Check your API key, "
                "quota and request limits."
            ) from error

        durations = matrix["durations"][0]
        distances = matrix["distances"][0]

        for i, hike in enumerate(batch):
            duration_seconds = durations[i]
            distance_metres = distances[i]

            # No usable route was returned
            if (
                duration_seconds is None
                or distance_metres is None
            ):
                continue

            duration_minutes = duration_seconds / 60

            # Keep hikes within the requested time limit
            if duration_minutes <= max_driving_time:
                result = hike.copy()

                result["driving_time_min"] = round(
                    duration_minutes
                )

                result["driving_distance_km"] = round(
                    distance_metres / 1000, 1
                )

                reachable_hikes.append(result)

    return reachable_hikes
  also


# --------------------------------------------------
# 5. Test the filter independently
# --------------------------------------------------

if __name__ == "__main__":

    with open(
        "hikes_data.json",
        "r",
        encoding="utf-8"
    ) as file:
        hikes = json.load(file)

    results = filter_hikes_by_car(
        hikes=hikes,
        start_location="Winterthur",
        max_driving_time=90
    )

    print("Reachable hikes:", len(results))

    for hike in results:
        print(
            hike["name"],
            "-",
            hike["driving_time_min"],
            "minutes by car -",
            hike["driving_distance_km"],
            "km"
        )
