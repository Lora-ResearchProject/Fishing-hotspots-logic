from pydantic import BaseModel

class FishingLocationRequest(BaseModel):
    id: str  # Vessel ID and Message ID separated by "|"
    l: str   # Latitude and Longitude separated by "|"
    f: int   # Indicator (whether this is fishing hotspot incoming message)

class LinkVesselHotspotRequest(BaseModel):
    vessel_id: str
    hotspot_id: int

class UnlinkVesselHotspotRequest(BaseModel):
    vessel_id: str

class VesselLocationRequest(BaseModel):
    id: str  # Vessel ID and Message ID separated by "|"
    l: str   # Latitude and Longitude separated by "|"