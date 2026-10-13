import csv
import json
import time
from datetime import datetime
import requests

API_URL = "https://api.open-meteo.com/v1/forecast"
CITIES_CSV = "data/cities.csv"
OUTPUT_FILE = "data/raw_weather_stream.jsonl"

def load_cities(filepath: str):
    """Load target cities and coordinates dynamically from CSV."""
    cities = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cities.append(
                {
                    "city_id": int(row["city_id"]),
                    "city_name": row["city_name"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                }
            )
    return cities

def fetch_weather(cities):
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Polling weather for {len(cities)} cities..."
    )

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        for city in cities:
            params = {
                "latitude": city["latitude"],
                "longitude": city["longitude"],
                "current": [
                    "temperature_2m",
                    "precipitation",
                    "wind_speed_10m",
                ],
            }
            try:
                response = requests.get(API_URL, params=params, timeout=10)
                response.raise_for_status()
                current = response.json().get("current", {})

                event = {
                    "timestamp": datetime.now().isoformat(),
                    "city_id": city["city_id"],
                    "city": city["city_name"],
                    "temperature_c": current.get("temperature_2m"),
                    "precipitation_mm": current.get("precipitation"),
                    "wind_speed_kmh": current.get("wind_speed_10m"),
                }

                f.write(json.dumps(event) + "\n")
                print(f" -> {city['city_name']}: {event['temperature_c']}°C")
            except Exception as e:
                print(f" -> Error fetching {city['city_name']}: {e}")

            time.sleep(1)

if __name__ == "__main__":
    target_cities = load_cities(CITIES_CSV)
    print("Starting simulated weather stream (Press Ctrl+C to stop)...")
    try:
        while True:
            fetch_weather(target_cities)
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nStream stopped.")