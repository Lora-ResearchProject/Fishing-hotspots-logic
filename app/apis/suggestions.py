import os
from fastapi import APIRouter, HTTPException
from ..database import fishing_locations, hotspots_vessels

router = APIRouter()

@router.get("/suggest_fishing_hotspots")
async def suggest_fishing_hotspots():
    """Suggest the latest available fishing hotspots."""
    try:
        # Fetch all active fishing hotspots
        active_hotspots = list(fishing_locations.find({"status": "active"}))
        
        # If no active hotspots exist, return an empty list
        if not active_hotspots:
            return {"status": "success", "message": "No active fishing hotspots available.", "data": []}

        # Filter out fully booked locations
        # Retrieve radius from the environment file
        max_vessels_per_hotspot = int(os.getenv("MAX_VESSELS_PER_HOTSPOT", 5))  # Default to 5 if not set
        available_hotspots = []
        for hotspot in active_hotspots:
            hotspot_id = hotspot.get("hotspotId")
            
            # Count vessels linked to this hotspot
            vessel_count = hotspots_vessels.count_documents({"hotspotId": hotspot_id})
            
            # Only include hotspots that are not fully booked
            if vessel_count < max_vessels_per_hotspot:
                available_hotspots.append({
                    "hotspotId": hotspot_id,
                    "latitude": hotspot.get("latitude"),
                    "longitude": hotspot.get("longitude"),
                    "currentDateTime": hotspot.get("currentDateTime"),
                    "vesselCount": vessel_count,  # Current number of vessels
                    "availableSlots": max_vessels_per_hotspot - vessel_count  # Remaining slots
                })

        # Sort the remaining hotspots by currentDateTime (latest first)
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
