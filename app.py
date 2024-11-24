from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import geopy.distance
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# MongoDB client setup
mongodb_url = os.getenv("MONGODB_URL")
if not mongodb_url:
    raise ValueError("MONGODB_URL is not set in the environment variables")

client = MongoClient(mongodb_url)
db = client['aquasafe']
fishing_locations = db['fishing_locations']

app = FastAPI()

MAX_DISTANCE_THRESHOLD = float(os.getenv("MAX_DISTANCE_THRESHOLD", "50"))
MAX_VISIT_THRESHOLD = int(os.getenv("MAX_VISIT_THRESHOLD", "10"))

# Request model for input coordinates
class LocationRequest(BaseModel):
    latitude: float
    longitude: float

# Function to get the best fishing location based on fuel efficiency and visit count
def get_best_fishing_location(current_latitude, current_longitude):
    locations = fishing_locations.find({"is_active": True})
    
    nearby_locations = []
    for location in locations:
        distance = geopy.distance.distance(
            (current_latitude, current_longitude),
            (location['latitude'], location['longitude'])
        ).km
        if distance < MAX_DISTANCE_THRESHOLD and location['visit_count'] < MAX_VISIT_THRESHOLD:
            nearby_locations.append((location, distance))
    
    # Sort locations by distance (for fuel efficiency) and visit count (for balance)
    sorted_locations = sorted(nearby_locations, key=lambda x: x[1])
    best_location = sorted_locations[0][0] if sorted_locations else None

    return {
        "latitude": best_location['latitude'],
        "longitude": best_location['longitude']
    } if best_location else None

# Adaptive learning function to update fishing location data based on wait time
def update_fishing_location(location_id, wait_time_minutes):
    fishing_location = fishing_locations.find_one({"_id": location_id})
    
    if wait_time_minutes > 30:
        new_avg_wait_time = (
            fishing_location['average_wait_time'] + wait_time_minutes
        ) / 2
        fishing_locations.update_one(
            {"_id": location_id},
            {"$set": {"average_wait_time": new_avg_wait_time, "is_active": True}}
        )
    deactivate_old_locations()

# Function to deactivate old locations not visited in the past 30 days
def deactivate_old_locations():
    cutoff_date = datetime.now() - timedelta(days=30)
    fishing_locations.update_many(
        {"last_visited": {"$lt": cutoff_date}},
        {"$set": {"is_active": False}}
    )

# GET endpoint to provide the best fishing hotspot recommendation
@app.get("/fishing_hotspots")
async def fishing_hotspots(latitude: float = Query(...), longitude: float = Query(...)):
    best_location = get_best_fishing_location(latitude, longitude)
    
    if best_location:
        return {
            "status": "success",
            "best_location": best_location
        }
    else:
        raise HTTPException(status_code=404, detail="No suitable fishing location found")


# To handle adaptive learning based on fishermen's wait time at a location
@app.post("/update_location")
async def update_location(location_id: str, wait_time_minutes: int):
    update_fishing_location(location_id, wait_time_minutes)
    return {"status": "updated"}
