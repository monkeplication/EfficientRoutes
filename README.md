# ⛽ EfficientRoutes — Fuel Route Planner API

A Django REST API that calculates the optimal fuel stops for a road trip across the USA, minimising fuel costs based on real gas prices.

---

## Features

- Takes a start and end city anywhere in the USA
- Returns the optimal fuel stops along the route based on cheapest state gas prices
- Assumes a vehicle range of 500 miles and 10 miles per gallon
- Calculates total fuel cost for the trip
- Serves an interactive map view showing the route and fuel stops
- Makes only 1 external API call (OSRM) per request — everything else runs locally

---

## Tech Stack

- **Django 6** + **Django REST Framework** — API framework
- **OSRM** (public endpoint) — free road routing, no API key required
- **Geopy / Nominatim** — city name to coordinates geocoding
- **Reverse Geocoder** — offline coordinate to US state lookup
- **Leaflet.js + CartoDB** — interactive map rendering in the browser

---

## Project Structure

```
EfficientRoutes/
├── manage.py
├── pyproject.toml
├── uv.lock
├── fuel_route/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── api/
    ├── views.py              # API endpoint + map view
    ├── utils.py              # Geocoding, OSRM routing, fuel price loader
    ├── urls.py               # URL routing
    ├── fuel-prices-for-be-assessment.csv
    └── templates/
        └── api/
            └── map.html      # Interactive Leaflet map
```

---

## Setup

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repo
git clone https://github.com/your-username/EfficientRoutes.git
cd EfficientRoutes

# Install dependencies
uv add django djangorestframework requests geopy reverse_geocoder

# Run the server
uv run python manage.py runserver
```

---

## API Usage

### `POST /api/route/`

Returns the optimal fuel stop plan as JSON.

**Request body:**
```json
{
    "start": "New York, NY",
    "end": "Los Angeles, CA"
}
```

**Response:**
```json
{
    "start": "New York, NY",
    "end": "Los Angeles, CA",
    "total_distance_miles": 2798.2,
    "fuel_stops": [
        {
            "lat": 41.024,
            "lon": -77.940,
            "state": "PA",
            "price_per_gallon": 3.259,
            "mile_marker": 391.5
        },
        ...
    ],
    "total_fuel_cost_usd": 890.26,
    "route_waypoints": [[40.712, -74.005], ...]
}
```

**Fields:**

| Field | Description |
|---|---|
| `total_distance_miles` | Total road distance from start to end |
| `fuel_stops` | Ordered list of optimal fuel stops |
| `total_fuel_cost_usd` | Total cost assuming 10 MPG |
| `route_waypoints` | Thinned list of coordinates for map rendering |

---

### `GET /api/map/`

Opens an interactive map in the browser showing the route and fuel stops.

```
http://127.0.0.1:8000/api/map/?start=New York, NY&end=Los Angeles, CA
```

---

## How the Fuel Optimization Works

1. **Geocode** the start and end city names into coordinates using Nominatim
2. **Fetch the route** from the OSRM public API — returns total distance and all waypoints along the road
3. **Sample waypoints** every ~1% of the route distance
4. At each sample point, use **reverse geocoder** (offline) to identify the US state
5. Trigger a fuel stop every time 75% of the 500-mile range is consumed
6. Pick the **cheapest available price** in that state from the fuel prices CSV
7. Calculate **total cost** as `(miles / 10 MPG) × price per gallon` for each leg

This approach makes only **1 external API call** (OSRM) per request. All fuel price lookups and state detection happen locally.

---

## Example Routes

| Route | Distance | Stops | Cost |
|---|---|---|---|
| New York, NY → Los Angeles, CA | 2,798 mi | 7 | $890 |
| Seattle, WA → Miami, FL | ~3,300 mi | 8 | ~$980 |
| Chicago, IL → Detroit, MI | ~280 mi | 1 | ~$85 |
