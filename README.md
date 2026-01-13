# Strava Data Backup

This project automatically backs up your Strava activities to a Git repository using GitHub Actions.

## Setup

### 1. Create a Strava Application
1. Go to [https://www.strava.com/settings/api](https://www.strava.com/settings/api).
2. Create an application:
    - **Category**: "Data Importer"
    - **Website**: "http://localhost"
    - **Authorization Callback Domain**: "localhost"
3. Note down the **Client ID** and **Client Secret**.

### 2. Get a Refresh Token
1. Construct the authorization URL in your browser:
   ```
   http://www.strava.com/oauth/authorize?client_id=[YOUR_CLIENT_ID]&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all
   ```
   Replace `[YOUR_CLIENT_ID]` with your actual Client ID.
2. Authorize the app.
3. You will be redirected to `http://localhost/exchange_token?state=&code=[AUTHORIZATION_CODE]&...`. Copy the `code`.
4. Exchange the authorization code for a refresh token using `curl` (or Postman):
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
   -F client_id=[YOUR_CLIENT_ID] \
   -F client_secret=[YOUR_CLIENT_SECRET] \
   -F code=[AUTHORIZATION_CODE] \
   -F grant_type=authorization_code
   ```
5. Note down the `refresh_token` from the response.

### 3. Configure GitHub Secrets
1. Go to your GitHub repository -> Settings -> Secrets and variables -> Actions.
2. Add the following repository secrets:
    - `STRAVA_CLIENT_ID`
    - `STRAVA_CLIENT_SECRET`
    - `STRAVA_REFRESH_TOKEN`

### 4. Workflow
The GitHub Action is scheduled to run daily at 00:00 UTC. It will:
1. Fetch new activities using the Python script.
2. Commit any new JSON files to the `activities/` directory.
3. Push the changes back to the repository.

## Local Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables:
   ```bash
   export STRAVA_CLIENT_ID=...
   export STRAVA_CLIENT_SECRET=...
   export STRAVA_REFRESH_TOKEN=...
   ```
3. Run the script:
   ```bash
   python backup.py
   ```
