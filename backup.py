import os
import requests
import json
import time

# Configuration
CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('STRAVA_REFRESH_TOKEN')

# Data Isolation: Use GITHUB_WORKSPACE if available (running as action)
WORKSPACE = os.environ.get('GITHUB_WORKSPACE', '.')
OUTPUT_DIR = os.environ.get('STRAVA_OUTPUT_DIR', 'activities')
ACTIVITIES_DIR = os.path.join(WORKSPACE, OUTPUT_DIR)

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

def get_activities(access_token, after=None):
    """Fetches activities from Strava. If after is provided, fetches only activities after that timestamp."""
    print("Fetching activities...")
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    all_activities = []
    page = 1
    per_page = 30
    
    while True:
        print(f"Fetching page {page}...")
        params = {'per_page': per_page, 'page': page}
        if after:
            params['after'] = after
            
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



def get_streams(activity_id, access_token):
    """Fetches activity streams (GPS, heart rate, etc)."""
    url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
    headers = {'Authorization': f'Bearer {access_token}'}
    keys = "time,latlng,distance,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth"
    params = {'keys': keys}
    
    try:
        res = requests.get(url, headers=headers, params=params, verify=False)
        if res.status_code == 200:
            return res.json()
        else:
            print(f"Failed to fetch streams for {activity_id}: {res.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching streams for {activity_id}: {e}")
        return None



def create_gpx(activity, streams):
    """Creates a GPX XML string from activity and streams."""
    from datetime import datetime
    
    gpx_header = """<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="StravaBackup" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">"""
    
    # Metadata
    name = activity.get('name', 'Activity')
    time_str = activity.get('start_date', '')
    gpx_metadata = f"""
 <metadata>
  <time>{time_str}</time>
 </metadata>
 <trk>
  <name>{name}</name>
  <trkseg>"""
  
    gpx_footer = """
  </trkseg>
 </trk>
</gpx>"""

    # Parse streams
    # streams is a list of dicts: [{'type': 'latlng', 'data': [...]}, {'type': 'time', 'data': [...]}, ...]
    # We need to pivot this to row-based data
    stream_map = {s['type']: s['data'] for s in streams}
    
    if 'latlng' not in stream_map or 'time' not in stream_map:
        return None
        
    latlngs = stream_map['latlng']
    times = stream_map['time'] # These are usually offsets or timestamps? Strava API usually returns epochs if not specified otherwise, but check. 
    # Actually streams 'time' is usually seconds from start. We need absolute time.
    # But wait, strava streams 'time' is elapsed time in seconds.
    # We need to construct absolute time.
    start_date_obj = datetime.strptime(activity['start_date'], "%Y-%m-%dT%H:%M:%SZ")
    start_timestamp = start_date_obj.timestamp()
    
    elevations = stream_map.get('altitude', [None] * len(latlngs))
    heartrates = stream_map.get('heartrate', [None] * len(latlngs))
    
    trkpts = ""
    for i in range(len(latlngs)):
        lat, lon = latlngs[i]
        ele = elevations[i]
        hr = heartrates[i]
        time_offset = times[i]
        
        # Calculate point time
        point_time = datetime.fromtimestamp(start_timestamp + time_offset).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        trkpts += f'\n   <trkpt lat="{lat}" lon="{lon}">'
        if ele is not None:
             trkpts += f'<ele>{ele}</ele>'
        trkpts += f'<time>{point_time}</time>'
        
        # Extension for HR (using TPX format commonly supported)
        if hr is not None:
            trkpts += f"""<extensions>
    <gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
     <gpxtpx:hr>{hr}</gpxtpx:hr>
    </gpxtpx:TrackPointExtension>
   </extensions>"""
            
        trkpts += '</trkpt>'
        
    # Inject xmlns for extension if needed
    if 'heartrate' in stream_map:
         gpx_header = gpx_header.replace('xmlns:xsi=', 'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1" xmlns:xsi=')

    return gpx_header + gpx_metadata + trkpts + gpx_footer

def save_activities(activities, access_token):
    """Saves activities to individual JSON files."""
    if not os.path.exists(ACTIVITIES_DIR):
        os.makedirs(ACTIVITIES_DIR)
        
    saved_count = 0
    for activity in activities:
        activity_id = activity['id']
        file_path = os.path.join(ACTIVITIES_DIR, f'{activity_id}.json')
        
        # Save activity summary
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(activity, f, indent=2)
            saved_count += 1
            
        # Check and save streams
        streams_file_path = os.path.join(ACTIVITIES_DIR, f'{activity_id}_streams.json')
        gpx_file_path = os.path.join(ACTIVITIES_DIR, f'{activity_id}.gpx')
        
        if not os.path.exists(streams_file_path) or not os.path.exists(gpx_file_path):
            streams = get_streams(activity_id, access_token)
            if streams:
                # Save Streams JSON
                if not os.path.exists(streams_file_path):
                    with open(streams_file_path, 'w') as f:
                        json.dump(streams, f, indent=2)
                    print(f"Saved streams for {activity_id}")

                # Save GPX
                if not os.path.exists(gpx_file_path):
                    gpx_content = create_gpx(activity, streams)
                    if gpx_content:
                        with open(gpx_file_path, 'w') as f:
                            f.write(gpx_content)
                        print(f"Saved GPX for {activity_id}")
                    else:
                        print(f"Skipped GPX for {activity_id} (missing latlng)")
                        
                # Rate limit safety
                time.sleep(1) 
            
    print(f"New activities saved: {saved_count}")

def main():
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        print("Error: Missing environment variables. Please set STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN.")
        exit(1)

    # Find the latest activity start date
    after_timestamp = None
    if os.path.exists(ACTIVITIES_DIR):
        latest_date = None
        for filename in os.listdir(ACTIVITIES_DIR):
            if filename.endswith('.json') and not filename.endswith('_streams.json'):
                try:
                    with open(os.path.join(ACTIVITIES_DIR, filename), 'r') as f:
                        activity_data = json.load(f)
                        start_date_str = activity_data.get('start_date')
                        if start_date_str:
                            from datetime import datetime
                            # Strava dates are in ISO 8601 format: 2024-02-19T23:04:46Z
                            start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%SZ")
                            if latest_date is None or start_date > latest_date:
                                latest_date = start_date
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        if latest_date:
            after_timestamp = int(latest_date.timestamp())
            print(f"Found latest activity date: {latest_date}. Fetching activities after {after_timestamp}")

    token = get_access_token()

    activities = get_activities(token, after=after_timestamp)
    save_activities(activities, token)

if __name__ == "__main__":
    main()
