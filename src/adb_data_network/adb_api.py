from dotenv import load_dotenv
import os
import time
import requests
import pandas as pd
from typing import Dict, List

# Load environment variables from .env file
load_dotenv()

# Get environment variables
api_key = os.getenv("ADB_PAT")
instance_url = os.getenv("ADB_INSTANCE_URL")

class GenieAPI:
    def __init__(self, url, token):
        self.url = url.rstrip('/')
        self.headers = {"Authorization": f"Bearer {token}"}

    def list_spaces(self):
        """Retrieve all available Genie spaces."""
        endpoint = f"{self.url}/api/2.0/genie/spaces"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json().get("spaces", [])

    def get_space_details(self, space_id):
        """Extract all information for a specific space ID."""
        # We use include_serialized_space=true to get full structural info
        endpoint = f"{self.url}/api/2.0/genie/spaces/{space_id}"
        params = {"include_serialized_space": "true"}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    if not instance_url or not api_key:
        print("Error: Missing ADB_INSTANCE_URL or ADB_PAT in .env file.")
    else:
        genie = GenieAPI(instance_url, api_key)
        
        try:
            print("--- Retrieving all Genie spaces ---")
            spaces = genie.list_spaces()
            
            if not spaces:
                print("No Genie spaces found.")
            else:
                print(f"Found {len(spaces)} spaces.")
                
                # Take the first space
                first_space = spaces[1]
                space_id = first_space['space_id']
                print(f"\n--- Extracting full details for: {first_space.get('name')} ({space_id}) ---")
                
                details = genie.get_space_details(space_id)
                
                # Print the full details (JSON)
                import json
                print(json.dumps(details, indent=2))
                
        except Exception as e:
            print(f"An error occurred: {e}")