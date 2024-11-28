from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..database import hotspots_vessels, fishing_locations, vessels_locations
from ..models import LinkVesselHotspotRequest,VesselLocationRequest
from ..utils import parse_location_data

router = APIRouter()

@router.post("/link_vessel_to_hotspot")
async def link_vessel_to_hotspot(request: LinkVesselHotspotRequest):
    vessel_id, hotspot_id = request.vessel_id, request.hotspot_id

    # Check hotspot exists
    if not fishing_locations.find_one({"hotspotId": hotspot_id}):
        raise HTTPException(status_code=404, detail=f"hotspotId {hotspot_id} not found")

    # Check if already linked
    if hotspots_vessels.find_one({"vesselId": vessel_id, "hotspotId": hotspot_id, "status": 1}):
        return {"status": "failed", "message": f"Vessel {vessel_id} already linked to hotspot {hotspot_id}."}

    # Save
    data = {"vesselId": vessel_id, "hotspotId": hotspot_id, "dateTime": datetime.now().isoformat(), "status": 1}
    hotspots_vessels.insert_one(data)
    return {"status": "success", "message": "Vessel linked successfully", "data": data}

@router.post("/save_vessel_location")
async def save_vessel_location(request: VesselLocationRequest):
    """
    Save vessel location to the vessels_locations collection.
    """
    try:
        # Parse the request to extract vessel ID and location
        vessel_id, message_id, latitude, longitude = parse_location_data(request)

        # Prepare the data to be saved
        data = {
            "vesselId": vessel_id,
            "dateTime": datetime.now().isoformat(),
            "lat": latitude,
            "lng": longitude,
        }

        # Insert the data into the vessels_locations collection
        result = vessels_locations.insert_one(data)

        # Convert ObjectId to string for the response
        response_data = {**data, "_id": str(result.inserted_id)}

        # Respond with a success message
        return {
            "status": "success",
            "message": "Vessel location saved successfully.",
            "data": response_data,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )