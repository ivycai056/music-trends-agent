
import os
import json
import html
import asyncio
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from google.cloud import storage
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types

from processing import process_tracks

load_dotenv()


# ==========================================================
# AGENT 1: DATA INGESTION
# Fetches the current top 50 tracks from the Last.fm API
# ==========================================================

class IngestionAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        print("1. Fetching music data from Last.fm...")

        api_key = os.getenv("LASTFM_API_KEY")

        if not api_key:
            raise ValueError("LASTFM_API_KEY is missing from .env")

        params = {
            "method": "chart.gettoptracks",
            "api_key": api_key,
            "format": "json",
            "limit": 50
        }

        response = await asyncio.to_thread(
            requests.get,
            "https://ws.audioscrobbler.com/2.0/",
            params=params,
            timeout=20
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(
                data.get("message", "Last.fm API error")
            )

        tracks = data["tracks"]["track"]

        ctx.session.state["raw_data"] = data

        print(f"Successfully retrieved {len(tracks)} tracks!")

        if False:
            yield


# ==========================================================
# AGENT 2: DATA PROCESSING
# Calculates popularity and engagement statistics
# ==========================================================

class ProcessingAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        print("2. Processing music data...")

        raw_data = ctx.session.state["raw_data"]
        tracks = raw_data["tracks"]["track"]

        processed_data = process_tracks(tracks)

        ctx.session.state["processed_data"] = processed_data

        print(
            f"Processed {processed_data['total_tracks']} tracks!"
        )

        print(
            f"Combined play counts: "
            f"{processed_data['total_plays']:,}"
        )

        if False:
            yield


# ==========================================================
# AGENT 3: CLOUD STORAGE
# Uploads raw and processed JSON to Google Cloud Storage
# ==========================================================

class StorageAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        print("3. Uploading data to Google Cloud Storage...")

        bucket_name = os.getenv("GCS_BUCKET_NAME")

        if not bucket_name:
            raise ValueError(
                "GCS_BUCKET_NAME is missing from .env"
            )

        raw_data = ctx.session.state["raw_data"]
        processed_data = ctx.session.state["processed_data"]

        timestamp = datetime.now(timezone.utc).strftime(
            "%Y%m%d_%H%M%S"
        )

        def upload_data():
            client = storage.Client()
            bucket = client.bucket(bucket_name)

            files = [
                (
                    f"raw/tracks_{timestamp}.json",
                    raw_data
                ),
                (
                    f"processed/music_analytics_{timestamp}.json",
                    processed_data
                )
            ]

            for filename, content in files:
                blob = bucket.blob(filename)

                blob.upload_from_string(
                    json.dumps(
                        content,
                        indent=2,
                        ensure_ascii=False
                    ),
                    content_type="application/json"
                )

                print(f"Uploaded: gs://{bucket_name}/{filename}")

        await asyncio.to_thread(upload_data)

        print("Cloud storage upload successful!")

        if False:
            yield


# ==========================================================
# AGENT 4: INTERACTIVE DASHBOARD
# Generates HTML with three interactive Chart.js charts
# ==========================================================

class DashboardAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext):
        print("4. Generating interactive HTML dashboard...")

        data = ctx.session.state["processed_data"]
        tracks = data["tracks"]

        # Top 10 tracks by cumulative play count
        top_songs = sorted(
            tracks,
            key=lambda t: t["playcount"],
            reverse=True
        )[:10]

        # Artists with the most tracks in the dataset
        top_artists = data["top_artists"][:10]

        # Top 10 tracks by plays per unique listener
        top_engagement = sorted(
            tracks,
            key=lambda t: t["plays_per_listener"],
            reverse=True
        )[:10]

        unique_artists = len(
            set(track["artist"] for track in tracks)
        )

        def song_label(track):
            return f"{track['song']} — {track['artist']}"

        def js_data(value):
            return json.dumps(
                value, ensure_ascii=False
            ).replace("<", "\\u003c")

        song_labels = js_data([
            song_label(track) for track in top_songs
        ])

        song_plays = js_data([
            track["playcount"] for track in top_songs
        ])

        artist_labels = js_data([
            artist["artist"] for artist in top_artists
        ])

        artist_counts = js_data([
            artist["track_count"] for artist in top_artists
        ])

        engagement_labels = js_data([
            song_label(track) for track in top_engagement
        ])

        engagement_values = js_data([
            track["plays_per_listener"]
            for track in top_engagement
        ])

        # Build HTML table
        rows = ""

        for rank, track in enumerate(top_songs, 1):
            rows += f"""
            <tr>
                <td>{rank}</td>
                <td>{html.escape(track['song'])}</td>
                <td>{html.escape(track['artist'])}</td>
                <td>{track['playcount']:,}</td>
                <td>{track['listeners']:,}</td>
                <td>{track['plays_per_listener']:.2f}</td>
            </tr>
            """

        generated_at = datetime.now(
            timezone.utc
        ).strftime("%B %d, %Y at %H:%M UTC")

        dashboard_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Music Trends Analytics Dashboard</title>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 35px;
            background: #101010;
            color: #ffffff;
            font-family: Arial, Helvetica, sans-serif;
        }

        .container {
            max-width: 1400px;
            margin: auto;
        }

        h1 {
            font-size: 38px;
            color: #1DB954;
            margin-bottom: 8px;
        }

        h2 {
            font-size: 21px;
            margin-top: 0;
        }

        .subtitle {
            color: #aaaaaa;
            margin-bottom: 30px;
        }

        .stats {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(220px, 1fr));
            gap: 18px;
            margin-bottom: 25px;
        }

        .stat-card {
            background: #222222;
            border: 1px solid #333333;
            border-radius: 14px;
            padding: 25px;
        }

        .stat-label {
            font-size: 14px;
            color: #aaaaaa;
        }

        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #1DB954;
            margin: 12px 0;
        }

        .charts {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(340px, 1fr));
            gap: 20px;
        }

        .chart-card {
            background: #202020;
            border: 1px solid #333333;
            border-radius: 14px;
            padding: 24px;
        }

        .chart-wide {
            grid-column: 1 / -1;
        }

        .chart-description {
            font-size: 13px;
            color: #aaaaaa;
            margin-bottom: 20px;
        }

        .chart-container {
            position: relative;
            height: 360px;
        }

        .chart-wide .chart-container {
            height: 440px;
        }

        .table-card {
            background: #202020;
            border: 1px solid #333333;
            border-radius: 14px;
            padding: 24px;
            margin-top: 22px;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid #393939;
        }

        th {
            color: #1DB954;
            font-size: 14px;
        }

        td {
            font-size: 14px;
        }

        tr:hover {
            background: #2d2d2d;
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            color: #888888;
            font-size: 13px;
            line-height: 1.8;
        }

        @media (max-width: 600px) {
            body {
                padding: 18px;
            }

            h1 {
                font-size: 28px;
            }

            .charts {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>
<div class="container">

    <h1>Music Trends Analytics</h1>

    <p class="subtitle">
        Powered by Last.fm API, Google ADK,
        and Google Cloud Storage
    </p>

    <!-- SUMMARY METRICS -->

    <div class="stats">

        <div class="stat-card">
            <div class="stat-label">Tracks Analyzed</div>
            <div class="stat-value">__TOTAL_TRACKS__</div>
            <div class="stat-label">
                Current Last.fm top tracks
            </div>
        </div>

        <div class="stat-card">
            <div class="stat-label">Combined Play Counts</div>
            <div class="stat-value">__TOTAL_PLAYS__</div>
            <div class="stat-label">
                Sum of cumulative track plays
            </div>
        </div>

        <div class="stat-card">
            <div class="stat-label">Unique Artists</div>
            <div class="stat-value">__UNIQUE_ARTISTS__</div>
            <div class="stat-label">
                Artists represented in the dataset
            </div>
        </div>

    </div>

    <!-- INTERACTIVE CHARTS -->

    <div class="charts">

        <div class="chart-card chart-wide">
            <h2>Top 10 Songs by Total Plays</h2>
            <p class="chart-description">
                Songs ranked by cumulative play count
                among the 50 charted tracks.
            </p>
            <div class="chart-container">
                <canvas id="songsChart"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h2>Most Represented Artists</h2>
            <p class="chart-description">
                Number of songs each artist has
                in the top 50.
            </p>
            <div class="chart-container">
                <canvas id="artistsChart"></canvas>
            </div>
        </div>

        <div class="chart-card">
            <h2>Plays per Listener</h2>
            <p class="chart-description">
                Total plays divided by unique listeners.
                Higher values indicate more repeat plays
                per listener on average.
            </p>
            <div class="chart-container">
                <canvas id="engagementChart"></canvas>
            </div>
        </div>

    </div>

    <!-- DATA TABLE -->

    <div class="table-card">

        <h2>Top 10 Songs by Play Count</h2>

        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Song</th>
                    <th>Artist</th>
                    <th>Total Plays</th>
                    <th>Listeners</th>
                    <th>Plays / Listener</th>
                </tr>
            </thead>

            <tbody>
                __TABLE_ROWS__
            </tbody>
        </table>

    </div>

    <div class="footer">
        <p>Generated: __GENERATED_AT__</p>
        <p>
            Data source: Last.fm chart.getTopTracks API.
            Play counts are cumulative, not daily streams.
        </p>
        <p>
            Agentic pipeline: Ingestion → Processing →
            Cloud Storage → Visualization
        </p>
    </div>

</div>

<script>

    const songLabels = __SONG_LABELS__;
    const songPlays = __SONG_PLAYS__;

    const artistLabels = __ARTIST_LABELS__;
    const artistCounts = __ARTIST_COUNTS__;

    const engagementLabels = __ENGAGEMENT_LABELS__;
    const engagementValues = __ENGAGEMENT_VALUES__;

    Chart.defaults.color = "#cccccc";
    Chart.defaults.borderColor = "#393939";

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: true
            }
        }
    };

    // CHART 1: TOP SONGS

    new Chart(
        document.getElementById("songsChart"),
        {
            type: "bar",

            data: {
                labels: songLabels,
                datasets: [{
                    label: "Total Plays",
                    data: songPlays,
                    backgroundColor: "#1DB954",
                    borderRadius: 5
                }]
            },

            options: {
                ...commonOptions,

                indexAxis: "y",

                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: value =>
                                Number(value).toLocaleString()
                        }
                    },

                    y: {
                        ticks: {
                            autoSkip: false,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        }
    );

    // CHART 2: TOP ARTISTS

    new Chart(
        document.getElementById("artistsChart"),
        {
            type: "bar",

            data: {
                labels: artistLabels,
                datasets: [{
                    label: "Charted Tracks",
                    data: artistCounts,
                    backgroundColor: "#1DB954",
                    borderRadius: 5
                }]
            },

            options: {
                ...commonOptions,

                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        }
    );

    // CHART 3: ENGAGEMENT

    new Chart(
        document.getElementById("engagementChart"),
        {
            type: "bar",

            data: {
                labels: engagementLabels,
                datasets: [{
                    label: "Plays per Listener",
                    data: engagementValues,
                    backgroundColor: "#55AAFF",
                    borderRadius: 5
                }]
            },

            options: {
                ...commonOptions,

                indexAxis: "y",

                scales: {
                    x: {
                        beginAtZero: true
                    },

                    y: {
                        ticks: {
                            autoSkip: false,
                            font: {
                                size: 10
                            }
                        }
                    }
                }
            }
        }
    );

</script>

</body>
</html>
"""

        replacements = {
            "__TOTAL_TRACKS__": str(data["total_tracks"]),
            "__TOTAL_PLAYS__": f"{data['total_plays']:,}",
            "__UNIQUE_ARTISTS__": str(unique_artists),
            "__TABLE_ROWS__": rows,
            "__GENERATED_AT__": generated_at,
            "__SONG_LABELS__": song_labels,
            "__SONG_PLAYS__": song_plays,
            "__ARTIST_LABELS__": artist_labels,
            "__ARTIST_COUNTS__": artist_counts,
            "__ENGAGEMENT_LABELS__": engagement_labels,
            "__ENGAGEMENT_VALUES__": engagement_values
        }

        for placeholder, value in replacements.items():
            dashboard_html = dashboard_html.replace(
                placeholder,
                value
            )

        os.makedirs("output", exist_ok=True)

        output_path = os.path.join(
            "output",
            "dashboard.html"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(dashboard_html)

        print(f"Dashboard created: {output_path}")

        if False:
            yield


# ==========================================================
# GOOGLE ADK SEQUENTIAL AGENT
# Orchestrates the four stages in order
# ==========================================================

root_agent = SequentialAgent(
    name="MusicTrendsPipeline",
    description=(
        "An agentic data engineering pipeline that fetches "
        "music trends, processes statistics, uploads results "
        "to cloud storage, and generates an HTML dashboard."
    ),
    sub_agents=[
        IngestionAgent(name="IngestionAgent"),
        ProcessingAgent(name="ProcessingAgent"),
        StorageAgent(name="StorageAgent"),
        DashboardAgent(name="DashboardAgent")
    ]
)


# ==========================================================
# RUN THE PIPELINE
# ==========================================================

async def main():

    runner = InMemoryRunner(
        agent=root_agent,
        app_name="music_trends"
    )

    session = await runner.session_service.create_session(
        app_name="music_trends",
        user_id="student"
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text="Run the complete music trends pipeline."
            )
        ]
    )

    async for event in runner.run_async(
        user_id="student",
        session_id=session.id,
        new_message=message
    ):
        pass

    print()
    print("=" * 55)
    print("MUSIC TRENDS PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 55)
    print("Dashboard: output/dashboard.html")
    print("Cloud data: Google Cloud Storage")
    print("Orchestration: Google Agent Development Kit")


if __name__ == "__main__":
    asyncio.run(main())
