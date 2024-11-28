from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB client setup
mongodb_url = os.getenv("MONGODB_URL")
if not mongodb_url:
    raise ValueError("MONGODB_URL is not set in the environment variables")

client = MongoClient(mongodb_url)
db = client['aquasafe']

# Collections
fishing_locations = db['fishing_hotspots_locations']
hotspots_vessels = db['hotspots_vessels']
vessels_locations = db['vessels_locations']
