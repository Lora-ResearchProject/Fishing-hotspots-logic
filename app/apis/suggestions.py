import os
import math
from fastapi import APIRouter, HTTPException, Query
from ..database import fishing_locations, hotspots_vessels

router = APIRouter()

def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two lat/lon pairs in kilometers 
    using the Haversine formula.
    """
    # Convert lat/long to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    # Radius of Earth in kilometers
    r = 6371  
    return c * r

@router.get("/suggest_fishing_hotspots")
async def suggest_fishing_hotspots(
    latitude: float = Query(..., description="User's current latitude"),
    longitude: float = Query(..., description="User's current longitude")
):
    """Suggest the latest available fishing hotspots within the maximum distance threshold."""
    try:
        # Fetch threshold from .env (default to 50 km if not set)
        max_distance_threshold = float(os.getenv("MAX_DISTANCE_THRESHOLD", 50.0))
        
        # Fetch all active fishing hotspots
        active_hotspots = list(fishing_locations.find({"status": "active"}))
        
        # If no active hotspots exist, return an empty list
        if not active_hotspots:
            return {"status": "success", "message": "No active fishing hotspots available.", "data": []}
        
        # Retrieve max vessels per hotspot from .env
        max_vessels_per_hotspot = int(os.getenv("MAX_VESSELS_PER_HOTSPOT", 5))
        
        available_hotspots = []
        for hotspot in active_hotspots:
            hotspot_id = hotspot.get("hotspotId")
            hotspot_lat = hotspot.get("latitude")
            hotspot_lon = hotspot.get("longitude")
            
            # Calculate distance from user’s lat/long to this hotspot
            distance_km = calculate_distance_km(
                latitude, 
                longitude, 
                float(hotspot_lat), 
                float(hotspot_lon)
            )
            
            # Only include hotspots within the max distance threshold
            if distance_km <= max_distance_threshold:
                # Count vessels linked to this hotspot
                vessel_count = hotspots_vessels.count_documents({"hotspotId": hotspot_id})
                
                # Only include hotspots that are not fully booked
                if vessel_count < max_vessels_per_hotspot:
                    available_hotspots.append({
                        "hotspotId": hotspot_id,
                        "latitude": hotspot_lat,
                        "longitude": hotspot_lon,
                        "currentDateTime": hotspot.get("currentDateTime"),
                        "vesselCount": vessel_count,
                        "availableSlots": max_vessels_per_hotspot - vessel_count,
                        "distanceKm": distance_km  # (Optional) Useful for debugging/UI
                    })

        # Sort by currentDateTime (latest first)
        available_hotspots.sort(key=lambda x: x["currentDateTime"], reverse=True)

        # Limit to the latest 3 locations
        latest_hotspots = available_hotspots[:3]

        return {
            "status": "success",
            "message": "Latest suggested fishing hotspots retrieved successfully.",
            "data": latest_hotspots
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
