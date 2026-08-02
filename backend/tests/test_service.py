"""Tests for the shared sync pipeline in service.perform_sync."""

import pytest

from app import app, db
from models import DislikedSong, SyncedTrack, TrackedPlaylist, User
import service
import spotify_client


def _playlist_data(uris):
    return {
        "name": "Test Playlist",
        "tracks": {
            "items": [{"track": {"uri": u}} for u in uris],
            "next": None,
        },
    }


@pytest.fixture()
def fresh_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def tracked_playlist_id(fresh_db):
    with app.app_context():
        user = User(id="service-test-user")
        db.session.add(user)
        db.session.flush()
        tp = TrackedPlaylist(
            user_id=user.id,
            source_playlist_id="source-1",
            tracked_playlist_id="tracked-1",
            tracked_playlist_name="Tracked One",
        )
        db.session.add(tp)
        db.session.commit()
        return tp.id


def _stub_spotify(monkeypatch, source_uris, tracked_uris, added_list):
    def fake_details(token, playlist_id):
        if playlist_id == "source-1":
            return _playlist_data(source_uris)
        return _playlist_data(tracked_uris)

    def fake_all_uris(token, playlist_data):
        return [item["track"]["uri"] for item in playlist_data["tracks"]["items"] if item.get("track") and item["track"].get("uri")]

    def fake_add(token, playlist_id, track_uris):
        added_list.extend(track_uris)

    monkeypatch.setattr(spotify_client, "get_playlist_details", fake_details)
    monkeypatch.setattr(spotify_client, "get_all_track_uris", fake_all_uris)
    monkeypatch.setattr(spotify_client, "add_tracks_to_playlist", fake_add)


def test_perform_sync_adds_only_new_source_tracks(monkeypatch, tracked_playlist_id):
    """Source has A, B, C; tracked has A; B was previously disliked -> only C is added."""
    added_list = []
    _stub_spotify(
        monkeypatch,
        source_uris=["spotify:track:A", "spotify:track:B", "spotify:track:C"],
        tracked_uris=["spotify:track:A"],
        added_list=added_list,
    )

    with app.app_context():
        tp = db.session.get(TrackedPlaylist, tracked_playlist_id)
        db.session.add(DislikedSong(song_uri="spotify:track:B", tracked_playlist_id=tp.id))
        db.session.add(SyncedTrack(track_uri="spotify:track:A", tracked_playlist_id=tp.id))
        db.session.commit()

        added = service.perform_sync(tp, "test-token")

        assert added == 1
        assert added_list == ["spotify:track:C"]

        snapshot = {t.track_uri for t in db.session.execute(
            db.select(SyncedTrack).where(SyncedTrack.tracked_playlist_id == tp.id)
        ).scalars().all()}
        assert snapshot == {"spotify:track:A", "spotify:track:C"}
        assert tp.last_synced is not None


def test_perform_sync_records_manually_removed_tracks_as_disliked(monkeypatch, tracked_playlist_id):
    """User removed B from the tracked playlist; the next sync records it as disliked."""
    added_list = []
    _stub_spotify(
        monkeypatch,
        source_uris=["spotify:track:A", "spotify:track:B"],
        tracked_uris=["spotify:track:A"],
        added_list=added_list,
    )

    with app.app_context():
        tp = db.session.get(TrackedPlaylist, tracked_playlist_id)
        # Last successful sync had A and B
        db.session.add_all([
            SyncedTrack(track_uri="spotify:track:A", tracked_playlist_id=tp.id),
            SyncedTrack(track_uri="spotify:track:B", tracked_playlist_id=tp.id),
        ])
        db.session.commit()

        added = service.perform_sync(tp, "test-token")

        assert added == 0
        assert added_list == []

        disliked_uris = {s.song_uri for s in db.session.execute(
            db.select(DislikedSong).where(DislikedSong.tracked_playlist_id == tp.id)
        ).scalars().all()}
        assert disliked_uris == {"spotify:track:B"}

        # B is not re-added and not in the new snapshot
        snapshot = {t.track_uri for t in db.session.execute(
            db.select(SyncedTrack).where(SyncedTrack.tracked_playlist_id == tp.id)
        ).scalars().all()}
        assert snapshot == {"spotify:track:A"}


def test_perform_sync_stale_snapshot_records_previously_removed_song(monkeypatch, tracked_playlist_id):
    """
    Latent-bug scenario: an auto-sync previously ran but left the DB snapshot stale,
    so a song removed from the tracked playlist is still in the snapshot. A subsequent
    (manual) sync must record it as disliked instead of re-adding it.
    """
    added_list = []
    _stub_spotify(
        monkeypatch,
        source_uris=["spotify:track:A", "spotify:track:X"],
        tracked_uris=["spotify:track:A"],
        added_list=added_list,
    )

    with app.app_context():
        tp = db.session.get(TrackedPlaylist, tracked_playlist_id)
        # Stale snapshot: X is present in the DB but no longer on Spotify
        db.session.add_all([
            SyncedTrack(track_uri="spotify:track:A", tracked_playlist_id=tp.id),
            SyncedTrack(track_uri="spotify:track:X", tracked_playlist_id=tp.id),
        ])
        db.session.commit()

        added = service.perform_sync(tp, "test-token")

        assert added == 0
        assert added_list == []

        disliked_uris = {s.song_uri for s in db.session.execute(
            db.select(DislikedSong).where(DislikedSong.tracked_playlist_id == tp.id)
        ).scalars().all()}
        assert disliked_uris == {"spotify:track:X"}

        snapshot = {t.track_uri for t in db.session.execute(
            db.select(SyncedTrack).where(SyncedTrack.tracked_playlist_id == tp.id)
        ).scalars().all()}
        assert snapshot == {"spotify:track:A"}


def test_perform_sync_returns_zero_when_up_to_date(monkeypatch, tracked_playlist_id):
    added_list = []
    _stub_spotify(
        monkeypatch,
        source_uris=["spotify:track:A", "spotify:track:B"],
        tracked_uris=["spotify:track:A", "spotify:track:B"],
        added_list=added_list,
    )

    with app.app_context():
        tp = db.session.get(TrackedPlaylist, tracked_playlist_id)
        db.session.add_all([
            SyncedTrack(track_uri="spotify:track:A", tracked_playlist_id=tp.id),
            SyncedTrack(track_uri="spotify:track:B", tracked_playlist_id=tp.id),
        ])
        db.session.commit()

        added = service.perform_sync(tp, "test-token")

        assert added == 0
        assert added_list == []
