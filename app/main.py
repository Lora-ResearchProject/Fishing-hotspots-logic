from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from .apis import hotspots, vessels, suggestions

app = FastAPI()

# Include routers
app.include_router(hotspots.router, tags=["Hotspots"])
app.include_router(vessels.router, tags=["Vessels"])
app.include_router(suggestions.router, tags=["Suggestions"])

# Scheduler setup
scheduler = BackgroundScheduler()

@app.on_event("startup")
def start_scheduler():
    scheduler.start()

@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown()

# Background job example
@scheduler.scheduled_job("interval", minutes=5)
def check_vessel_activity():
    pass
