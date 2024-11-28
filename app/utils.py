import math
from fastapi import HTTPException
from .database import fishing_locations

def parse_location_data(request):
    """Parse and validate location data."""
    try:
        vessel_id, message_id = request.id.split("|")
        latitude, longitude = map(float, request.l.split("|"))
        latitude = round(latitude, 5)
        longitude = round(longitude, 5)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid format for 'id' or 'l'")
    return vessel_id, message_id, latitude, longitude

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance using the Haversine formula."""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_next_hotspot_id():
    """Determine the next available hotspotId."""
    last_hotspot = fishing_locations.find_one({}, sort=[("hotspotId", -1)], projection={"hotspotId": 1})
    return 1 if not last_hotspot else last_hotspot["hotspotId"] + 1

from fastapi import HTTPException

def parse_location_data(request):
    """Parse and validate location data."""
    try:
        # Split ID into vessel ID and message ID
        vessel_id, message_id = request.id.split("|")

        # Split location into latitude and longitude
        latitude, longitude = map(float, request.l.split("|"))
        latitude = round(latitude, 5)
        longitude = round(longitude, 5)

    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid format for 'id' or 'l'"
        )

    return vessel_id, message_id, latitude, longitude

