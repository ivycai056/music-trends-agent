
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("LASTFM_API_KEY")

print("Starting Last.fm API test...")

if not API_KEY:
    raise ValueError("API key not found! Check your .env file.")

url = "https://ws.audioscrobbler.com/2.0/"

params = {
    "method": "chart.gettoptracks",
    "api_key": API_KEY,
    "format": "json",
    "limit": 50
}

print("Connecting to Last.fm...")

response = requests.get(url, params=params, timeout=20)
response.raise_for_status()

data = response.json()

if "error" in data:
    raise RuntimeError(data.get("message", "Last.fm API error"))

tracks = data["tracks"]["track"]

print(f"Successfully retrieved {len(tracks)} tracks!")

for track in tracks[:10]:
    print(
        track["name"],
        "-",
        track["artist"]["name"],
        "| Plays:",
        track["playcount"]
    )
