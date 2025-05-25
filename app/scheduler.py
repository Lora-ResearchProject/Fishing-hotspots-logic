from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .database import hotspots_vessels, vessels_locations

# Create the scheduler instance
scheduler = BackgroundScheduler(timezone="UTC") 

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
        active_count = hotspots_vessels.find({"status": 1})

        if active_count == 0:
            print(f"[{now.isoformat()}] No active vessels found in hotspots_vessels.")
        else:
            # Iterate only once – reuse the cursor
            for vessel in hotspots_vessels.find({"status": 1}):
                vessel_id  = vessel["vesselId"]
                hotspot_id = vessel["hotspotId"]

                activity_count = vessels_locations.count_documents({
                    "vesselId": vessel_id,
                    "timestamp": {"$gte": fifteen_minutes_ago}
                })

                if activity_count == 0:
                    hotspots_vessels.update_one(
                        {"_id": vessel["_id"]},
                        {"$set": {"status": 0}}
                    )
                    print(
                        f"[{now.isoformat()}] Updated vessel {vessel_id} at "
                        f"hotspot {hotspot_id} to inactive."
                    )

            print(f"[{now.isoformat()}] check_vessel_activity completed.")

    except Exception as e:
        print(f"An error occurred in check_vessel_activity: {e}")


# Add jobs to the scheduler
scheduler.add_job(check_vessel_activity, "interval", minutes=1)
