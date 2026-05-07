import reverse_geocoder as rg
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .utils import geocode_city, get_route, FUEL_PRICES


@api_view(["POST"])
def get_fuel_route(request):
    start_city = request.data.get("start")
    end_city = request.data.get("end")

    if not start_city or not end_city:
        return Response(
            {"error": "Please provide both start and end city."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Cities to coordinates
    start_coords = geocode_city(start_city)
    end_coords = geocode_city(end_city)

    if not start_coords or not end_coords:
        return Response(
            {"error": "Could not geocode one or both cities."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Route from Osrm
    route = get_route(start_coords, end_coords)
    if not route:
        return Response(
            {"error": "Could not get route from OSRM."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    total_miles = route["distance_miles"]
    waypoints = route["waypoints"]

    # Finding optimal fuel routes
    MAX_RANGE = 500  # miles
    MPG = 10
    fuel_stops = []
    total_cost = 0.0
    miles_since_last_fill = 0
    num_waypoints = len(waypoints)

    # Sample every Nth waypoint to avoid checking thousands of points
    step = max(1, num_waypoints // 100)

    for i in range(0, num_waypoints, step):
        lat, lon = waypoints[i]
        miles_covered = (i / num_waypoints) * total_miles
        miles_since_last_fill = miles_covered - (
            fuel_stops[-1]["mile_marker"] if fuel_stops else 0
        )

        if miles_since_last_fill >= MAX_RANGE * 0.75:
            # Look up state for this coordinate
            result = rg.search((lat, lon), verbose=False)
            state_code = result[0].get("admin1", "")

            # Map full state name to abbreviation
            state_abbr = get_state_abbr(state_code)
            price = FUEL_PRICES.get(state_abbr)

            if price:
                fuel_stops.append({
                    "lat": lat,
                    "lon": lon,
                    "state": state_abbr,
                    "price_per_gallon": price,
                    "mile_marker": round(miles_covered, 1),
                })

    for i, stop in enumerate(fuel_stops):
        if i == 0:
            miles = stop["mile_marker"]
        else:
            miles = stop["mile_marker"] - fuel_stops[i - 1]["mile_marker"]
        gallons = miles / MPG
        total_cost += gallons * stop["price_per_gallon"]

    # Add final leg cost
    last_marker = fuel_stops[-1]["mile_marker"] if fuel_stops else 0
    final_miles = total_miles - last_marker
    if fuel_stops:
        total_cost += (final_miles / MPG) * fuel_stops[-1]["price_per_gallon"]

    return Response({
        "start": start_city,
        "end": end_city,
        "total_distance_miles": round(total_miles, 1),
        "fuel_stops": fuel_stops,
        "total_fuel_cost_usd": round(total_cost, 2),
        "route_waypoints": waypoints[::50],  # thinned for map display
    })

#Yes, all the states of the great United States...
STATE_NAMES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

def get_state_abbr(full_name):
    return STATE_NAMES.get(full_name, full_name[:2].upper())