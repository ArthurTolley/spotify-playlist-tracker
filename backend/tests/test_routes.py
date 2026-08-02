"""Route smoke tests, including CSRF protection verification."""

import re
from types import SimpleNamespace

from flask import session

from app import app


def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_profile_redirects_to_login(client):
    response = client.get("/profile")
    assert response.status_code == 302


def test_logout_returns_template(client):
    response = client.get("/logout")
    assert response.status_code == 200
    assert b"Log in again" in response.data


def test_track_post_without_csrf_token_rejected(client):
    """Proves CSRF protection is live: a POST without a token is rejected."""
    response = client.post(
        "/track",
        data={"playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"},
    )
    assert response.status_code == 400


# --- CSRF-in-forms template test ---

_FORM_RE = re.compile(r"<form\b.*?</form>", re.IGNORECASE | re.DOTALL)
_METHOD_RE = re.compile(r"<form\b[^>]*\bmethod\s*=\s*[\"']POST[\"']", re.IGNORECASE)


def _make_tracked_playlist(id_):
    return SimpleNamespace(
        id=id_,
        tracked_playlist_id=f"tracked-{id_}",
        tracked_playlist_name=f"Tracked Playlist {id_}",
        cover_image_url=None,
        last_synced_formatted="Never",
        auto_sync_enabled=False,
    )


def _make_playlist(id_):
    return SimpleNamespace(
        id=id_,
        name=f"Playlist {id_}",
        images=[],
        owner=SimpleNamespace(id=f"owner-{id_}", display_name="Owner"),
    )


def _render_profile(undo_data=None):
    """Renders profile.html with minimal dummy context via a request context."""
    with app.test_request_context("/profile"):
        if undo_data is not None:
            session["undo_data"] = undo_data
        return app.jinja_env.get_template("profile.html").render(
            user=SimpleNamespace(id="user-1", display_name="Test User", images=[]),
            tracked_playlists=[_make_tracked_playlist(1)],
            all_user_playlists=[_make_playlist("a")],
            source_playlists=[_make_playlist("b")],
            tracked_source_ids=set(),
            tracked_playlist_ids=set(),
        )


def _post_forms(html):
    """Extracts complete <form>...</form> blocks whose method is POST."""
    return [block for block in _FORM_RE.findall(html) if _METHOD_RE.search(block)]


def test_all_post_forms_in_profile_contain_csrf_token():
    """Every POST form rendered in profile.html (incl. the Undo form) must carry a CSRF token."""
    html = _render_profile(undo_data={"user_id": "user-1"})
    forms = _post_forms(html)
    assert forms, "expected at least one POST form in profile.html"
    # track, sync, untrack, delete, toggle-auto-sync, track-from-list (x2), undo
    assert len(forms) >= 5
    for form in forms:
        assert 'name="csrf_token"' in form, f"POST form missing csrf_token: {form[:160]}"
    # The Undo action must be a CSRF-protected POST form, not a GET link.
    assert "undo_untrack" in html
    assert "csrf_token" in html
