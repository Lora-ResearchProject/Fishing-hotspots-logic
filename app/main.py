from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from .apis import hotspots, vessels, suggestions

app = FastAPI()

# Enable CORS for all origins (Allow all requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

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


# Custom exception handler for 404 errors
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.method == "GET":
        return JSONResponse(content={"message": "Sorry!, Please make a valid Request!"}, status_code=404)
    return JSONResponse(content={"message": "Not Found - check 1"}, status_code=404)