
from collections import Counter


def process_tracks(tracks):
    processed = []

    for track in tracks:
        plays = int(track.get("playcount", 0))
        listeners = int(track.get("listeners", 0))

        processed.append({
            "song": track["name"],
            "artist": track["artist"]["name"],
            "playcount": plays,
            "listeners": listeners,
            "plays_per_listener": round(
                plays / listeners, 2
            ) if listeners > 0 else 0
        })

    artist_counts = Counter(
        track["artist"] for track in processed
    )

    return {
        "tracks": processed,
        "top_artists": [
            {"artist": artist, "track_count": count}
            for artist, count in artist_counts.most_common(10)
        ],
        "total_tracks": len(processed),
        "total_plays": sum(
            track["playcount"] for track in processed
        )
    }
