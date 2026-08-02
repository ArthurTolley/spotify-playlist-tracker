import requests
import json
import logging
import time

# --- Direct Spotify API Client using 'requests' ---

def _get_with_retry(url: str, headers: dict, retries: int = 3) -> requests.Response:
    """
    GET with retry on transient failures:
    - 429 (rate limited): honors the Retry-After header (seconds), default 1s
    - 5xx (server errors): exponential backoff (1s, 2s, 4s)
    Returns the last response after retries are exhausted so callers can
    raise_for_status() and handle the HTTPError as before.
    """
    attempt = 0
    while True:
        attempt += 1
        response = requests.get(url, headers=headers)

        if response.status_code == 429 and attempt <= retries:
            # Backoff delay (1s, 2s, 4s) doubles as the default/fallback delay.
            delay = min(2 ** (attempt - 1), 5)
            retry_after = response.headers.get('Retry-After')
            if retry_after:
                try:
                    # Retry-After can be seconds or an HTTP-date; only seconds are supported here.
                    delay = min(float(retry_after), 5)
                except ValueError:
                    # HTTP-date or garbage — fall back to the backoff delay.
                    pass
            logging.warning(f"Rate limited (429) fetching {url}; retrying in {delay}s (attempt {attempt}/{retries})")
            time.sleep(delay)
            continue

        if response.status_code >= 500 and attempt <= retries:
            delay = min(2 ** (attempt - 1), 5)  # 1s, 2s, 4s, capped at 5s
            logging.warning(f"Server error {response.status_code} fetching {url}; retrying in {delay}s (attempt {attempt}/{retries})")
            time.sleep(delay)
            continue

        return response

def get_playlist_details(token: str, playlist_id: str) -> dict:
    """
    Fetches the full details of a specific playlist using a direct API call.
    """
    api_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {token}"}

    logging.info(f"Fetching details for playlist: {playlist_id}")
    response = _get_with_retry(api_url, headers)

    # Raise an error for bad status codes (4xx or 5xx)
    response.raise_for_status()

    return response.json()


def get_all_track_uris(token: str, playlist_data: dict) -> list:
    """
    Fetches all track URIs from a playlist, handling pagination automatically.
    """
    tracks = []
    # Start with the first page of tracks from the initial playlist data
    for item in playlist_data['tracks']['items']:
        if item.get('track') and item['track'].get('uri'):
            tracks.append(item['track']['uri'])

    # Follow the 'next' link to get subsequent pages
    next_url = playlist_data['tracks'].get('next')
    headers = {"Authorization": f"Bearer {token}"}

    while next_url:
        logging.info("Fetching next page of tracks...")
        response = _get_with_retry(next_url, headers)
        response.raise_for_status()
        next_page_data = response.json()

        for item in next_page_data['items']:
            if item.get('track') and item['track'].get('uri'):
                tracks.append(item['track']['uri'])

        next_url = next_page_data.get('next')

    logging.info(f"Found a total of {len(tracks)} tracks.")
    return tracks


def create_new_playlist(token: str, user_id: str, playlist_name: str, description: str) -> str:
    """
    Creates a new empty playlist for a user.
    Returns the ID of the new playlist.
    """
    api_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {
        "name": playlist_name,
        "public": True,
        "description": description,
    }

    logging.info(f"Creating new playlist: {playlist_name}")
    response = requests.post(api_url, headers=headers, data=json.dumps(data))
    response.raise_for_status()

    playlist_id = response.json().get('id')
    logging.info(f"Playlist created with ID: {playlist_id}")
    return playlist_id


def add_tracks_to_playlist(token: str, playlist_id: str, track_uris: list):
    """
    Adds a list of tracks to a specified playlist.
    """
    api_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Spotify API can only handle 100 tracks at a time
    for i in range(0, len(track_uris), 100):
        chunk = track_uris[i:i+100]
        data = {"uris": chunk}

        logging.info(f"Adding {len(chunk)} tracks to playlist {playlist_id}")
        response = requests.post(api_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

