from app import parse_playlist_id


def test_parse_playlist_id_from_spotify_url():
    url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    assert parse_playlist_id(url) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_playlist_id_from_spotify_url_with_query_params():
    url = "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc123"
    assert parse_playlist_id(url) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_playlist_id_from_uri():
    uri = "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M"
    assert parse_playlist_id(uri) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_playlist_id_from_raw_id():
    raw_id = "37i9dQZF1DXcBWIGoYBM5M"
    assert parse_playlist_id(raw_id) == "37i9dQZF1DXcBWIGoYBM5M"


def test_parse_playlist_id_rejects_invalid_strings():
    assert parse_playlist_id("https://open.spotify.com/playlist/not-a-valid-id") is None
    assert parse_playlist_id("spotify:album:37i9dQZF1DXcBWIGoYBM5M") is None
    assert parse_playlist_id("https://open.spotify.com/track/37i9dQZF1DXcBWIGoYBM5M") is None
    assert parse_playlist_id("short") is None
    assert parse_playlist_id("") is None


def test_parse_playlist_id_handles_none():
    assert parse_playlist_id(None) is None
