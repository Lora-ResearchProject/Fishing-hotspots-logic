from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
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

# GET endpoint to retrieve fishing locations by period
@router.get("/get_fishing_locations")
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
