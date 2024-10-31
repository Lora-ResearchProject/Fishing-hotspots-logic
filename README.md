# FISHING HOTSPOTS LOGIC

## Description

This is a model that develops a fishing spot prediction system to help anglers identify optimal fishing locations. The model considers factors such as fuel efficiency, environmental sustainability, and adaptive learning from historical data to suggest productive fishing spots while balancing ecosystem impact.

## Usage

The system provides an API that can be queried with a latitude and longitude to receive recommendations on the best fishing locations. The model takes into account recent activity and visit patterns to distribute fishermen evenly and conserve fish populations. Additionally, the system learns over time, adjusting hotspots based on live fishing patterns.

## Installation

### For macOs:

1. Rename .example.env file into .env and fill the reqeusted configuration within the file
1. Create python virtual environment `python3 -m venv venv`
1. Active the virtual environment `source venv/bin/activate`
1. Command to diactivate the virtual environment (if needed) `deactivate`
1. Install all the dependencies `pip install -r requirements.txt`
1. Start the server `uvicorn app:app --reload`

### Other commands:

1. Generate the requirements.txt file `pip freeze > requirements.txt`

## API Integration

1.  Get Best Fishing Location

        - Endpoint: `/fishing_hotspots`
        - Method: `GET`
        - Query Parameters:
          - `latitude` (float): Latitude of the current location.
          - `longitude` (float): Longitude of the current location.
        - Description: Returns the optimal fishing location based on fuel efficiency, visit count, and historical hotspot data.
        - Example Request:
          - `GET http://127.0.0.1:8000/fishing_hotspots?latitude=56.127788&longitude=12.310137`
        - Example Response: - `{
        "status": "success",
        "best_location": {
            "latitude": 56.130000,
            "longitude": 12.315000
        }

    }`

2.  Update Location Data (Adaptive Learning)
    - Endpoint: `/update_location`
    - Method: `POST`
    - Body:
      - location_id (string): Unique identifier for the fishing location.
      - wait_time_minutes (integer): Time (in minutes) that a fisherman waited at a location.
    - Description: Updates the model with time spent at a location, helping it adapt to popular hotspots and deactivating unused spots.
    - Example Request:
      - ` POST http://127.0.0.1:8000/update_location
{
"location_id": "211477000-3",
"wait_time_minutes": 35
} `
    - Example Response:
        - `{
    "status": "updated"
}`


## Compatible versions

## Deployment
