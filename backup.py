import os
import requests
import json
import time

# Configuration
CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('STRAVA_REFRESH_TOKEN')
ACTIVITIES_DIR = 'activities'

def get_access_token():
    """Exchanges the refresh token for a new access token."""
    print("Refreshing access token...")
    auth_url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token',
        'f': 'json'
    }
    res = requests.post(auth_url, data=payload, verify=False)
    try:
        access_token = res.json()['access_token']
        print("Access token refreshed successfully.")
        return access_token
    except KeyError:
        print(f"Error refreshing token: {res.text}")
        exit(1)

def get_activities(access_token):
    """Fetches all activities from Strava."""
    print("Fetching activities...")
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    all_activities = []
    page = 1
    per_page = 30
    
    while True:
        print(f"Fetching page {page}...")
        params = {'per_page': per_page, 'page': page}
        res = requests.get(activities_url, headers=headers, params=params, verify=False)
        data = res.json()
        
        if not data:
            break
        
        if isinstance(data, dict) and 'message' in data: # Error handling
             print(f"Error fetching activities: {data}")
             break
             
        all_activities.extend(data)
        page += 1
        
    print(f"Total activities fetched: {len(all_activities)}")
    return all_activities

def save_activities(activities):
    """Saves activities to individual JSON files."""
    if not os.path.exists(ACTIVITIES_DIR):
        os.makedirs(ACTIVITIES_DIR)
        
    saved_count = 0
    for activity in activities:
        activity_id = activity['id']
        file_path = os.path.join(ACTIVITIES_DIR, f'{activity_id}.json')
        
        # Only save if file doesn't exist or we want to update (optional logic)
        # For backup, we might want to overwrite to get latest stats? 
        # But usually activities don't change much after upload.
        # Let's check if it exists to be efficient.
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(activity, f, indent=2)
            saved_count += 1
            
    print(f"New activities saved: {saved_count}")

def main():
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("Error: Missing environment variables. Please set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN.")
        exit(1)

    token = get_access_token()
    activities = get_activities(token)
    save_activities(activities)

if __name__ == "__main__":
    main()
