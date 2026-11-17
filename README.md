# Music Trends Analytics Agent

## Project Overview

This project is an end-to-end agentic data engineering pipeline built using Python and Google's Agent Development Kit (ADK).

The system retrieves music popularity data from the Last.fm API, processes the data, uploads raw and processed datasets to Google Cloud Storage, and generates an interactive HTML analytics dashboard.

## Technologies Used

- Python 3.11
- Google Agent Development Kit (ADK)
- Last.fm API
- Google Cloud Storage
- Chart.js
- HTML, CSS, and JavaScript

## Agent Workflow

The pipeline uses Google ADK's `SequentialAgent` to coordinate four custom agents:

1. **Ingestion Agent:** Retrieves the current top 50 tracks from the Last.fm API.
2. **Processing Agent:** Calculates total plays, listener counts, plays per listener, and artist representation.
3. **Storage Agent:** Uploads raw and processed JSON datasets to Google Cloud Storage.
4. **Dashboard Agent:** Generates an interactive HTML dashboard.

### Pipeline Architecture

Last.fm API → Ingestion Agent → Processing Agent → Storage Agent → Dashboard Agent → HTML Dashboard

## Dashboard Features

The dashboard includes:

- Total tracks analyzed
- Combined cumulative play counts
- Number of unique artists
- Top 10 songs ranked by total plays
- Artists with the most songs in the dataset
- Plays per listener
- Interactive charts and a detailed data table

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/music-trends-agent.git
cd music-trends-agent
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` into a new file named `.env`.

Add your own Last.fm API key and Google Cloud Storage bucket name:

```dotenv
LASTFM_API_KEY=your_api_key
GCS_BUCKET_NAME=your_bucket_name
```

You can obtain a Last.fm API key from https://www.last.fm/api.

### 5. Configure Google Cloud Storage

Create a Google Cloud project and Cloud Storage bucket.

Install the Google Cloud CLI and run:

```bash
gcloud auth application-default login
```

Ensure your Google Cloud account has permission to upload objects to the bucket.

### 6. Run the pipeline

```bash
python agent.py
```

The pipeline will automatically execute all four agents.

### 7. View the dashboard

Open:

`output/dashboard.html`

The dashboard uses Chart.js, which requires an internet connection to load its charts.

## Cloud Storage Output

The pipeline saves timestamped JSON files to Google Cloud Storage:

- `raw/tracks_YYYYMMDD_HHMMSS.json`
- `processed/music_analytics_YYYYMMDD_HHMMSS.json`

## Data Interpretation

Last.fm play counts represent cumulative reported plays rather than daily streaming activity.

The dashboard compares the tracks returned by one API request. It does not yet measure changes in popularity over time.

## Future Improvements

Potential enhancements include:

- Scheduling the pipeline to run automatically every day.
- Collecting historical data to identify changes in music popularity.
- Integrating additional music APIs.
- Adding automated data quality checks.
- Hosting the dashboard online.

## Security

API keys and local credentials are excluded from GitHub using `.gitignore`. The repository includes `.env.example` to document the required configuration without exposing private values.