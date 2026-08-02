"""
Shared sync pipeline used by both the manual /sync route and the auto-sync scheduler job.

Keeping this logic in one place ensures manual and automatic syncs behave identically
(e.g., both record newly disliked songs and rebuild the DB snapshot).
"""
import logging
from datetime import datetime, timezone

import spotify_client
from models import db, DislikedSong, SyncedTrack


def perform_sync(tracked_playlist, token) -> int:
    """
    Runs the full sync pipeline for a tracked playlist.

    - Fetches the source playlist's tracks from Spotify
    - Fetches the user's tracked playlist's tracks from Spotify
    - Records songs the user manually removed (present in the last DB snapshot but
      missing from the tracked playlist) as disliked
    - Adds new source songs that are not already in the tracked playlist and not disliked
    - Rebuilds the DB snapshot to match the post-sync state
    - Updates ``last_synced`` and commits

    Returns the number of songs added to the tracked playlist.
    """
    # --- STEP 1: Get all current states ---
    # Get songs from the original source playlist on Spotify
    source_data = spotify_client.get_playlist_details(token, tracked_playlist.source_playlist_id)
    source_uris = set(spotify_client.get_all_track_uris(token, source_data))

    # Get songs currently in the user's tracked playlist on Spotify
    tracked_data = spotify_client.get_playlist_details(token, tracked_playlist.tracked_playlist_id)
    current_tracked_uris = set(spotify_client.get_all_track_uris(token, tracked_data))

    # Get the snapshot of tracks from our DB from the LAST successful sync
    previous_synced_tracks = db.session.execute(
        db.select(SyncedTrack).where(SyncedTrack.tracked_playlist_id == tracked_playlist.id)
    ).scalars().all()
    previous_synced_uris = {t.track_uri for t in previous_synced_tracks}

    # Get all songs the user has ever disliked for this playlist
    disliked_songs_db = db.session.execute(
        db.select(DislikedSong).where(DislikedSong.tracked_playlist_id == tracked_playlist.id)
    ).scalars().all()
    disliked_uris = {s.song_uri for s in disliked_songs_db}

    # --- STEP 2: Find songs the user manually removed (the new "disliked" songs) ---
    # A song was removed by the user if it was in our last snapshot, but is NOT in the playlist now.
    newly_disliked_uris = previous_synced_uris - current_tracked_uris

    if newly_disliked_uris:
        for uri in newly_disliked_uris:
            # Add to disliked table only if it's not already there
            if uri not in disliked_uris:
                db.session.add(DislikedSong(song_uri=uri, tracked_playlist_id=tracked_playlist.id))

        # Update our in-memory set of disliked songs for the next step
        disliked_uris.update(newly_disliked_uris)
        logging.info(f"Recorded {len(newly_disliked_uris)} newly disliked songs.")

    # --- STEP 3: Find new songs to add to the tracked playlist ---
    # A song should be added if it's in the source, not already in the tracked playlist,
    # AND not in our master list of disliked songs.
    songs_to_add = list(source_uris - current_tracked_uris - disliked_uris)

    if songs_to_add:
        spotify_client.add_tracks_to_playlist(token, tracked_playlist.tracked_playlist_id, songs_to_add)

    # --- STEP 4: Update the DB snapshot to the new state ---
    # The new "correct" state is what's currently on Spotify plus the songs we just added.
    new_snapshot_uris = current_tracked_uris.union(songs_to_add)

    # Delete the old snapshot, then save the new one in bulk
    db.session.execute(db.delete(SyncedTrack).where(SyncedTrack.tracked_playlist_id == tracked_playlist.id))
    db.session.add_all([
        SyncedTrack(track_uri=uri, tracked_playlist_id=tracked_playlist.id)
        for uri in new_snapshot_uris
    ])

    # Finally, update the sync timestamp and commit all changes
    tracked_playlist.last_synced = datetime.now(timezone.utc)
    db.session.commit()

    return len(songs_to_add)
