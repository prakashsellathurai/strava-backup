# Strava Data Backup

![GitHub License](https://img.shields.io/github/license/prakashsellathurai/strava-backup)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/prakashsellathurai/strava-backup)


This project automatically backs up your Strava activities to a Git repository using GitHub Actions. It fetches your activities using the Strava API and saves them as individual JSON files in the `activities/` directory.

## Project Structure

- `backup.py`: The main script that fetches activities from Strava and saves them locally.
- `get_refresh_token.py`: A helper script to generate the necessary Refresh Token for API access.
- `.github/workflows/backup.yaml`: The GitHub Action workflow definition that runs the backup daily.
- `activities/`: Directory where activity data is stored (one JSON file per activity).

## Prerequisites

- Python 3.9 or higher
- A Strava account
- Git

## Usage as a GitHub Action

You can use this repository directly in your own GitHub Action to automate Strava backups.

### Pre-requisites
1.  **Create a Strava API Application**: Go to [Strava Settings](https://www.strava.com/settings/api) and create an application.
2.  **Get a Refresh Token**: Use the `get_refresh_token.py` script in this repository or follow the OAuth flow to get a refresh token with `activity:read_all` scope.
3.  **Add Secrets**: In your GitHub repository settings, add the following secrets:
    - `STRAVA_CLIENT_ID`
    - `STRAVA_CLIENT_SECRET`
    - `STRAVA_REFRESH_TOKEN`

### Usage
To use this action in your own repository, create a workflow file (e.g., `.github/workflows/backup.yml`):

```yaml
name: Strava Backup

on:
  schedule:
    - cron: '0 0 * * *' # Run daily at midnight
  workflow_dispatch:

permissions:
  contents: write

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Strava Backup
        uses: prakashsellathurai/strava-backup@main
        with:
          client_id: ${{ secrets.STRAVA_CLIENT_ID }}
          client_secret: ${{ secrets.STRAVA_CLIENT_SECRET }}
          refresh_token: ${{ secrets.STRAVA_REFRESH_TOKEN }}
```

> [!IMPORTANT]
> **Workflow Permissions**: You must ensure that your repository settings allow GitHub Actions to write to the repository. 
> 1. Go to **Settings > Actions > General**.
> 2. Under **Workflow permissions**, select **"Read and write permissions"**.
> 3. Click **Save**.

## Setup

### 1. Create a Strava Application

1. Go to [https://www.strava.com/settings/api](https://www.strava.com/settings/api).
2. Create an application:
    - **Category**: "Data Importer"
    - **Website**: "http://localhost"
    - **Authorization Callback Domain**: "localhost"
3. Note down the **Client ID** and **Client Secret**.

### 2. Local Setup and Token Generation

It is recommended to use a virtual environment.

1.  Clone the repository and enter the directory:
    ```bash
    git clone https://github.com/prakashsellathurai/strava-backup
    cd strava-backup
    ```

2.  Create and activate a virtual environment:
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Run the helper script to get your Refresh Token:
    ```bash
    python get_refresh_token.py
    ```
    Follow the on-screen prompts. You will need your Client ID and Client Secret from Step 1.

### 3. Configure GitHub Secrets

1. Go to your GitHub repository -> Settings -> Secrets and variables -> Actions.
2. Add the following repository secrets:
    - `STRAVA_CLIENT_ID`: Your Client ID.
    - `STRAVA_CLIENT_SECRET`: Your Client Secret.
    - `STRAVA_REFRESH_TOKEN`: The Refresh Token generated in Step 2.

## Usage

### Automated Backup (GitHub Actions)
The configured GitHub Action runs automatically every 3 days at 00:00 UTC. It will:
1. Fetch new activities.
2. Commit any new or updated JSON files to the `activities/` directory.
3. Push the changes to the repository.

You can also manually trigger the "Strava Backup" workflow from the "Actions" tab in your repository.

### Manual Local Backup

To run the backup manually on your machine:

1.  Set the environment variables (replace with your values):
    ```bash
    # Windows (PowerShell)
    $env:STRAVA_CLIENT_ID="your_client_id"
    $env:STRAVA_CLIENT_SECRET="your_client_secret"
    $env:STRAVA_REFRESH_TOKEN="your_refresh_token"

    # macOS/Linux
    export STRAVA_CLIENT_ID="your_client_id"
    export STRAVA_CLIENT_SECRET="your_client_secret"
    export STRAVA_REFRESH_TOKEN="your_refresh_token"
    ```

2.  Run the backup script:
    ```bash
    python backup.py
    ```

## Troubleshooting

### Token Expiration
If the backup starts failing with authentication errors, your Refresh Token might have expired or been revoked. Run `get_refresh_token.py` again to generate a new one and update your GitHub Secret.

### Missing Activities
The script fetches activities in pages of 30. If you have a very large number of activities, the initial backup might take some time. The script prints its progress.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
