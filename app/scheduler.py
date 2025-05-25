import os
import math
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from .database import hotspots_vessels, vessels_locations, fishing_locations

# Create the scheduler instance
scheduler = BackgroundScheduler(timezone="UTC") 

# ------------------------------------------------------------
# Job 1 ------------------------------------------------------

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



# ------------------------------------------------------------
# Job 2  – save_fishing_location trigger -----------------

MAX_DISTANCE_M = float(os.getenv("MAX_DISTANCE_THRESHOLD", "1000"))  # metres
API_BASE_URL   = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
SAVE_URL       = f"{API_BASE_URL}/save_fishing_location"


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in *metres* between two lat/lon points."""
    R = 6_371_000  # Earth radius in metres
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(d_lon / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def scan_fishing_activity():
    """
    For each vessel that has location records in the last hour, calculate
    the straight-line distance covered.  If distance ≤ MAX_DISTANCE_M,
    POST a fishing-location record.
    """
    try:
        now_iso = datetime.utcnow().isoformat()
        window_start_iso = (datetime.utcnow() - timedelta(minutes=60)).isoformat()

        # Every vessel that reported at least once in the last 60 min
        vessel_ids = vessels_locations.distinct(
            "vesselId", {"dateTime": {"$gte": window_start_iso}}
        )

        for vessel_id in vessel_ids:
            # Oldest → newest track points in the window
            track = list(
                vessels_locations.find(
                    {"vesselId": vessel_id, "dateTime": {"$gte": window_start_iso}}
                ).sort("dateTime", 1)
            )
            if len(track) < 2:
                continue  # not enough data

            first, last = track[0], track[-1]
            dist_m = haversine_m(
                float(first["lat"]), float(first["lng"]),
                float(last["lat"]),  float(last["lng"])
            )

            if dist_m <= MAX_DISTANCE_M:
                payload = {
                    "id": f"{int(vessel_id):03d}|0001",
                    "l":  f'{last["lat"]}|{last["lng"]}',
                    "f": 1
                }
                try:
                    requests.post(SAVE_URL, json=payload, timeout=10)
                    print(
                        f"[{now_iso}] Fishing spot saved for vessel {vessel_id} "
                        f"(travelled {dist_m:.0f} m ≤ {MAX_DISTANCE_M} m)"
                    )
                except Exception as e:
                    print(f"[Scheduler] POST to save_fishing_location failed: {e}")

        print(f"[{now_iso}] scan_fishing_activity finished.")

    except Exception as e:
        print(f"[Scheduler] scan_fishing_activity error: {e}")


# Run this job every 1 minutes (adjust as needed)
scheduler.add_job(scan_fishing_activity, "interval", minutes=1)

# ------------------------------------------------------------
# Job 3  – remove the unused hotspots trigger -----------------

UNUSED_HOTSPOT_DAYS = int(os.getenv("UNUSED_HOTSPOT_DAYS", "3"))
CHECK_INTERVAL_MIN = UNUSED_HOTSPOT_DAYS * 24 * 60


def deactivate_unused_hotspots():
    """
    Every N days:
    • Look back N days in `hotspots_vessels`
    • Collect hotspotIds that *have* been used in that window
    • Any hotspot still marked active in `fishing_locations`
      but *not* in that list → set status to 'inactive'.
    """
    try:
        now_utc   = datetime.utcnow()
        cutoff_iso = (now_utc - timedelta(days=UNUSED_HOTSPOT_DAYS)).isoformat()

        # hotspotIds used in the look-back window
        recent_hotspots = hotspots_vessels.distinct(
            "hotspotId",
            {"dateTime": {"$gte": cutoff_iso}}
        )
        recent_set = set(recent_hotspots)

        # All hotspots still flagged active
        unused_cursor = fishing_locations.find({
            "status": "active",
            "hotspotId": {"$nin": list(recent_set)}
        })

        changed = 0
        for doc in unused_cursor:
            fishing_locations.update_one(
                {"_id": doc["_id"]},
                {"$set": {"status": "inactive",
                          "inactivatedDateTime": now_utc.isoformat()}}
            )
            changed += 1
            print(f"[{now_utc.isoformat()}] Hotspot {doc['hotspotId']} set inactive.")

        print(f"[{now_utc.isoformat()}] deactivate_unused_hotspots finished – "
              f"{changed} hotspot(s) updated.")

    except Exception as e:
        print(f"[Scheduler] deactivate_unused_hotspots error: {e}")


# Register the job (interval = N days)
scheduler.add_job(
    deactivate_unused_hotspots,
    "interval",
    minutes=CHECK_INTERVAL_MIN,
    id="deactivate_unused_hotspots"
)
