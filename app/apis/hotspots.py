from fastapi import APIRouter
from datetime import datetime
import os
from ..database import fishing_locations
from ..models import FishingLocationRequest
from ..utils import parse_location_data, haversine, get_next_hotspot_id

router = APIRouter()

@router.post("/save_fishing_location")
async def save_fishing_location(request: FishingLocationRequest):
    vessel_id, message_id, latitude, longitude = parse_location_data(request)

    # Retrieve radius from the environment file
    radius_in_meters = float(os.getenv("LOCATION_RADIUS_METERS", 20))  # Default to 20 meters if not set
    if any(
        haversine(latitude, longitude, loc["latitude"], loc["longitude"]) <= radius_in_meters
        for loc in fishing_locations.find({"status": "active"})
    ):
        return {"status": "failed", "message": "Location exists within the radius.", "radius": radius_in_meters}

    # Save location
    hotspot_id = get_next_hotspot_id()
    data = {
        "hotspotId": hotspot_id,
        "vesselId": vessel_id,
        "messageId": message_id,
        "latitude": latitude,
        "longitude": longitude,
        "currentDateTime": datetime.now().isoformat(),
        "status": "active",
        "f": request.f,
    }
    result = fishing_locations.insert_one(data)

    # Add the inserted ID as a string to the response
    data["_id"] = str(result.inserted_id)

    return {"status": "success", "message": "Fishing location saved successfully", "data": data}
