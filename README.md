# FISHING HOTSPOTS LOGIC

## Description

This is a logic that develops a fishing spot prediction system to help anglers identify optimal fishing locations. The logic considers factors such as fuel efficiency, environmental sustainability, and adaptive learning from historical data to suggest productive fishing spots while balancing ecosystem impact.

## Usage

The system provides an API that can be queried with a latitude and longitude to receive recommendations on the best fishing locations. The logic takes into account recent activity and visit patterns to distribute fishermen evenly and conserve fish populations. Additionally, the system learns over time, adjusting hotspots based on live fishing patterns.

## Installation

### For macOs:

1. Rename .example.env file into .env and fill the reqeusted configuration within the file
2. Create python virtual environment `python3 -m venv venv`
3. Active the virtual environment `source venv/bin/activate`
4. Command to diactivate the virtual environment (if needed) `deactivate`
5. Install all the dependencies `pip install -r requirements.txt`
6. Start the server `uvicorn app:app --reload`

### Other commands:

1. Generate the requirements.txt file `pip freeze > requirements.txt`

## API Integration

### Save Fishing Location

* **Endpoint: POST /save_fishing_location**
* This API endpoint is used to save fishing hotspot data to the database.
* Requested Parameteres:
  * id (string): Vessel ID and Message ID separated  by a hyphen (-)
  * l (string): Latitude and Longitude saparated by a hyphen (-)
  * f (integer): Indicator (used to mark whether this is a fishing hotspot message)
* Reqeusted Body Example:
  ```
  {
    "id": "123-4567",
    "l": "12.2323-34.23432",
    "f": 1
  }
  ```
* Response:
  * Success:

    ```
    {
      "status": "success",
      "message": "Fishing location saved successfully",
      "data": {
        "vesselId": "123",
        "messageId": "4567",
        "latitude": 12.2323,
        "longitude": 34.23432,
        "currentDateTime": "2024-11-25T15:30:00.123456",
        "status": "active",
        "f": 1,
        "_id": "6521c7d7afdbf3e4d8a75f4a"
      }
    }
    ```
  * Failure (Duplicate Location):

    ```
    {
      "status": "failed",
      "message": "Location already exists within the specified radius.",
      "radius": 20
    }
    ```

### Get Fishing Locations

* **Endpoint: GET /get_fishing_locations**
* This API endpoint retrieves fishing location details based on the specified time period or date range.
* Query Parameters:
  * period (string) *(optional)*: Filtered by predefined periods:
    * "month": Locations from the last 30days.
    * "year": Locations from the current year.
    * "last year": Locations from the previous year.
  * start_date (string) *(optional)*: Custom start date in YYYY-MM-DD format.
  * end_date (string) *(optional)*: Custom end date in YYYY-MM-DD format.
* if period is provided, start_date and the end_date are ignored.
* Query parameter Examples:
  * Get location for the last month:

    ```
    /get_fishing_locations?period=month
    ```
  * Get location for this year:

    ```
    /get_fishing_locations?period=year
    ```
  * Get location for last year:

    ```
    /get_fishing_locations?period=last%20year
    ```
  * Get locations for a custom date range:

    ```
    /get_fishing_locations?start_date=2024-10-01&end_date=2024-12-01
    ```

## Compatible versions

## Deployment
