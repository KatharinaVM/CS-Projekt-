import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SWITZERLAND_API_KEY")


url = "https://opendata.myswitzerland.io/v1/tours"

headers = {
    "x-api-key": API_KEY
}

url = "https://opendata.myswitzerland.io/v1/tours"

params = {
    "facet.filter": [
        "origin:schweiz-mobil",
        "routestypes:hike"
    ]
}

response = requests.get(url, headers=headers, params=params)
hikes = response.json()["data"]

hiking_data = []

for item in hikes[:3]:

    # Get detailed information
    detail_url = item["links"]["self"]
    detail = requests.get(detail_url, headers=headers).json()["data"]

    specs = detail.get("specs", {})
    mobility = detail.get("switzerlandMobility", {})
    geo = detail.get("geo", {})

    # Convert classifications into a useful dictionary
    classifications = {}

    for c in detail.get("classification", []):
        if "name" in c:
            classifications[c["name"]] = [
                v.get("name") for v in c.get("values", [])
            ]

    # Collect all images
    images = [
        image.get("url")
        for image in detail.get("image", [])
        if image.get("url")
    ]

    # Collect itinerary places
    itinerary = [
        place.get("name")
        for place in detail.get("itinerary", [])
        if place.get("name")
    ]

# Get full route geometry
geodata_url = mobility.get("geodata")
route_geometry = None

if geodata_url:
    geo_response = requests.get(geodata_url, headers=headers)

    if geo_response.status_code == 200:
        route_geometry = geo_response.json()

    hike = {
        "id": detail.get("identifier"),
        "name": detail.get("name"),
        "description": detail.get("abstract"),

        "distance_km": specs.get("distance"),
        "duration_min": specs.get("duration"),
        "ascent_m": specs.get("ascent"),
        "descent_m": specs.get("descent"),
        "season": specs.get("season"),
        "barrier_free": specs.get("barrierFree"),

        "latitude": geo.get("latitude"),
        "longitude": geo.get("longitude"),

        "technical_difficulty": mobility.get("requirements", {}).get("technical"),
        "endurance_difficulty": mobility.get("requirements", {}).get("endurance"),
        "route_category": mobility.get("routeCategory"),
        "stage": mobility.get("stage"),

        "classifications": classifications,
        "images": images,
        "itinerary": itinerary,

        "myswitzerland_url": detail.get("url"),
        "schweizmobil_url": mobility.get("url"),
        "geodata_url": mobility.get("geodata"),
        "route_geometry": route_geometry
    }

    hiking_data.append(hike)

with open("hikes_data.json", "w", encoding="utf-8") as file:
    json.dump(hiking_data, file, ensure_ascii=False, indent=2)

print("Saved", len(hiking_data), "hikes to hikes_data.json")