from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .database import hotspots_vessels, vessels_locations

# Create the scheduler instance
scheduler = BackgroundScheduler()

def check_vessel_activity():
    """
    Background task to check vessel activity and update statuses.
    If no activity is found for a vessel in the last 15 minutes, mark it inactive.
    """
    try:
        # Define the time range (last 15 minutes)
        now = datetime.now()
        fifteen_minutes_ago = now - timedelta(minutes=15)

        # Get all vessels with status = 1 in hotspots_vessels
        active_vessels = hotspots_vessels.find({"status": 1})

        # Check activity for each active vessel
        for vessel in active_vessels:
            vessel_id = vessel["vesselId"]
            hotspot_id = vessel["hotspotId"]

            # Check if the vessel has any activity in the last 15 minutes
            activity_count = vessels_locations.count_documents({
                "vesselId": vessel_id,
                "hotspotId": hotspot_id,
                "timestamp": {"$gte": fifteen_minutes_ago}
            })

            # If no activity is found, update status to 0
            if activity_count == 0:
                hotspots_vessels.update_one(
                    {"_id": vessel["_id"]},
                    {"$set": {"status": 0}}
                )
                print(f"Updated vessel {vessel_id} at hotspot {hotspot_id} to inactive.")

    except Exception as e:
        print(f"An error occurred in check_vessel_activity: {e}")


# Add jobs to the scheduler
scheduler.add_job(check_vessel_activity, "interval", minutes=1)
