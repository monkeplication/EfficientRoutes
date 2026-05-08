import csv
import os
import requests
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="fuel_route_app")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "fuel-prices-for-be-assessment.csv")

# Load once at startup — cheapest price per state
def load_fuel_prices():
    prices = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            state = row["State"].strip()
            try:
                price = float(row["Retail Price"])
            except ValueError:
                continue
            if state not in prices or price < prices[state]:
                prices[state] = price
    return prices

FUEL_PRICES = load_fuel_prices()


def geocode_city(city_name):
    # Convert city name to coordinates
    location = geolocator.geocode(f"{city_name}, USA")
    if not location:
        return None
    return (location.latitude, location.longitude)


def get_route(start_coords, end_coords):
    
    start = f"{start_coords[1]},{start_coords[0]}"
    end = f"{end_coords[1]},{end_coords[0]}"

    url = (
        f"http://router.project-osrm.org/route/v1/driving/{start};{end}"
        f"?overview=full&geometries=geojson&steps=false"
    )

    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("code") != "Ok":
        return None

    route = data["routes"][0]
    distance_meters = route["distance"]
    distance_miles = distance_meters / 1609.34

    # Extract waypoints from geojson coordinates
    coords = route["geometry"]["coordinates"]
    # coords are [lon, lat] - flip to (lat, lon)
    waypoints = [(c[1], c[0]) for c in coords]

    return {
        "distance_miles": distance_miles,
        "waypoints": waypoints,
    }