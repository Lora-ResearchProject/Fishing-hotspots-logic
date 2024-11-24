from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv()

# MongoDB client setup
mongodb_url = os.getenv("MONGODB_URL")
if not mongodb_url:
    raise ValueError("MONGODB_URL is not set in the environment variables")

client = MongoClient(mongodb_url)
db = client['aquasafe']
fishing_locations = db['fishing_locations']

# Get circle radius from .env
radius_in_meters = float(os.getenv("LOCATION_RADIUS_METERS", 20))  # Default to 20 meters

app = FastAPI()

# Request model
class FishingLocationRequest(BaseModel):
    id: str  # Vessel ID and Message ID separated by "-"
    l: str   # Latitude and Longitude separated by "-"
    f: int   # Indicator (whether this is fishing hotspot incoming message)


# Utility to parse and validate input
def parse_location_data(request: FishingLocationRequest):
    try:
        vessel_id, message_id = request.id.split("-")
        latitude, longitude = map(float, request.l.split("-"))
        # Limit precision to 5 decimal places
        latitude = round(latitude, 5)
        longitude = round(longitude, 5)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid format for 'id' or 'l'"
        )
    return vessel_id, message_id, latitude, longitude


# Utility to calculate distance using the Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Function to check if the location is within the radius of any existing location
def is_location_within_radius(latitude, longitude):
    existing_locations = fishing_locations.find({"status": "active"})  # Check only active locations
    for location in existing_locations:
        db_lat = round(location["latitude"], 5)
        db_lon = round(location["longitude"], 5)
        distance = haversine(latitude, longitude, db_lat, db_lon)
        if distance <= radius_in_meters:
            return True
    return False


# POST endpoint to save fishing hotspot data
@app.post("/save_fishing_location")
async def save_fishing_location(request: FishingLocationRequest):
    # Parse and validate input
    vessel_id, message_id, latitude, longitude = parse_location_data(request)

    # Check if the location is within the radius of existing locations
    if is_location_within_radius(latitude, longitude):
        return {
            "status": "failed",
            "message": "Location already exists within the specified radius.",
            "radius": radius_in_meters
        }

    # Prepare data for saving
    current_time = datetime.now().isoformat()
    data = {
        "vesselId": vessel_id,
        "messageId": message_id,
        "latitude": latitude,
        "longitude": longitude,
        "currentDateTime": current_time,
        "status": "active",  # Default status as active
        "f": request.f       # Save the indicator as-is
    }

    # Save to the database
    result = fishing_locations.insert_one(data)

    # Add the inserted ID as a string to the response
    data["_id"] = str(result.inserted_id)

    return {"status": "success", "message": "Fishing location saved successfully", "data": data}


# GET endpoint to retrieve fishing locations by period
@app.get("/get_fishing_locations")
async def get_fishing_locations(
    period: str = Query(None, description="Filter by 'month', 'year', 'last year', or a date range"),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format (optional if period is given)"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format (optional if period is given)")
):
    try:
        # Determine the date range based on period
        now = datetime.now()
        if period == "month":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        elif period == "year":
            start_date = datetime(now.year, 1, 1).strftime("%Y-%m-%d")
            end_date = datetime(now.year, 12, 31).strftime("%Y-%m-%d")
        elif period == "last year":
            start_date = datetime(now.year - 1, 1, 1).strftime("%Y-%m-%d")
            end_date = datetime(now.year - 1, 12, 31).strftime("%Y-%m-%d")
        elif start_date and end_date:
            # Use custom date range
            pass
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid query parameters. Specify a valid period or a start and end date."
            )

        # Convert start_date and end_date to datetime objects
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")

        # Query the database for locations in the specified date range
        query = {
            "currentDateTime": {
                "$gte": start_datetime.isoformat(),
                "$lte": end_datetime.isoformat()
            }
        }
        results = list(fishing_locations.find(query, {"_id": 0}))

        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")