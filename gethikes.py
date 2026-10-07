import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SWITZERLAND_API_KEY")
REQUEST_DELAY = 1.1


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

def api_get(url, **kwargs):
    time.sleep(REQUEST_DELAY)
    response = requests.get(url, headers=headers, **kwargs)
    response.raise_for_status()
    return response

# Remember which page should be loaded next
PROGRESS_FILE = "hiking_progress.json"

if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        progress = json.load(file)
        page_to_load = progress.get("next_page", 0)
else:
    # Start with page 0
    page_to_load = 0

PAGES_PER_RUN = 20

# Load existing hiking data
if os.path.exists("hikes_data.json"):
    with open("hikes_data.json", "r", encoding="utf-8") as file:
        hiking_data = json.load(file)
else:
    hiking_data = []

existing_ids = {hike["id"] for hike in hiking_data}

# Process one page at a time
for page in range(page_to_load, page_to_load + PAGES_PER_RUN):

    print(f"Processing page {page}...")

    page_params = params.copy()
    page_params["page"] = page

    response = api_get(url, params=page_params)
    hikes = response.json()["data"]

    for item in hikes:

        if item.get("identifier") in existing_ids:
            continue

        # Get detailed information
        detail_url = item["links"]["self"]
        detail = api_get(detail_url).json()["data"]

        specs = detail.get("specs", {})
        mobility = detail.get("switzerlandMobility", {})
        geo = detail.get("geo", {})

        # Classifications
        classifications = {}

        for c in detail.get("classification", []):
            if "name" in c:
                classifications[c["name"]] = [
                    v.get("name")
                    for v in c.get("values", [])
                ]

        # Images
        images = [
            image.get("url")
            for image in detail.get("image", [])
            if image.get("url")
        ]

        # Itinerary
        itinerary = [
            place.get("name")
            for place in detail.get("itinerary", [])
            if place.get("name")
        ]

        # Get route geometry
        geodata_url = mobility.get("geodata")
        route_points = []

        if geodata_url:
            geo_data = api_get(geodata_url).json()

            coordinates = []

            for feature in geo_data.get("features", []):
                geometry = feature.get("geometry", {})
                geometry_type = geometry.get("type")
                coords = geometry.get("coordinates", [])

                if geometry_type == "LineString":
                    coordinates.extend(coords)

                elif geometry_type == "MultiLineString":
                    for line in coords:
                        coordinates.extend(line)

            if coordinates:

                # Start + 5 intermediate points + end
                indices = [
                    round(i * (len(coordinates) - 1) / 6)
                    for i in range(7)
                ]

                route_points = [
                    [coordinates[i][1], coordinates[i][0]]
                    for i in indices
                ]

        # Skip routes without usable geometry
        if not route_points:
            continue

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

            "technical_difficulty":
                mobility.get("requirements", {}).get("technical"),

            "endurance_difficulty":
                mobility.get("requirements", {}).get("endurance"),

            "route_category": mobility.get("routeCategory"),
            "stage": mobility.get("stage"),

            "classifications": classifications,
            "images": images,
            "itinerary": itinerary,

            "myswitzerland_url": detail.get("url"),
            "schweizmobil_url": mobility.get("url"),
            "route_points": route_points
        }

        hiking_data.append(hike)
        existing_ids.add(hike["id"])

    # Save after EVERY page
    with open("hikes_data.json", "w", encoding="utf-8") as file:
        json.dump(
            hiking_data,
            file,
            ensure_ascii=False,
            indent=2
        )

    # Remember that this page is finished
    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump({"next_page": page + 1}, file)

    print(
        f"Page {page} complete - "
        f"{len(hiking_data)} hikes saved"
    )

print("Finished.")