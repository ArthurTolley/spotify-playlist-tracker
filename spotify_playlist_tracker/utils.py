import os
import requests
import json
import datetime
import logging

from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

load_dotenv()

def get_access_token() -> str:
    """Create an access token to access the Spotify API.

    Returns
    -------
    token : str
        The access token generated.

    Raises
    ------
        ValueError: If Spotify API credentials are not set.
    """

    # Call Spotify Developer credentials from Environment Variables
    client_id = os.environ.get('SPOTIPY_CLIENT_ID')
    client_secret = os.environ.get('SPOTIPY_CLIENT_SECRET')
    redirect_uri = 'http://localhost:8888/callback'

    if not client_id or not client_secret:
        raise ValueError("Spotify API credentials not set")

    auth = SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope='playlist-modify-public')

    token_info = auth.get_access_token()
    token = token_info.get('access_token')

    logging.info("Access token generated successfully.")

    return token

def get_user_playlists(token : str,
                       user_id : str) -> dict:
    """Fetches the playlists of a user.

    Parameters
    ----------
        token : str
            The access token for the Spotify API.
        user_id : str
            The user ID of the Spotify user.

    Returns
    -------
        dict
            A dictionary containing the playlist names and playlist IDs.
            The dictionary has the following structure:
            {
                'playlist_names': [str],
                'playlist_ids': [str]
            }
            If the request fails, None is returned.
    """
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)

    logging.info(f"Retrieving playlists for user {user_id}.")
    if response.status_code == 200:
        playlists_data = response.json()['items']
        num_playlists = len(response.json()['items'])
        playlist_names = [playlists_data[i]['name'] for i in range(num_playlists)]
        playlist_ids = [playlists_data[i]['id'] for i in range(num_playlists)]
        logging.info(f"  {num_playlists} playlists found")
        return {'playlist_names' : playlist_names,
                'playlist_ids' : playlist_ids}
    else:
        logging.error(f"Failed to retrieve playlists. Status code: {response.status_code}")
        return None

def get_playlist_tracks(token : str,
                        playlist_id : str) -> list:
    """Fetch the track ids for a specific playlist id.

    Parameters
    ----------
        token : str
            The access token for the Spotify API.
        playlist_id : str
            The ID of the playlist.

    Returns
    -------
        all_tracks : list
            A list of track IDs for the playlist.
    """

    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(playlist_url, headers=headers)
    playlist_data = response.json()

    if response.status_code == 200:
        playlist_name = playlist_data['name']
        owner_name = playlist_data['owner']['display_name']
        track_information = playlist_data['tracks']
        logging.info(f"Reading playlist: {playlist_name} by {owner_name}")

        if track_information['next'] is None:
            tracklist = track_information['items']
        else:
            tracklist = track_information['items']

            while len(track_information['items']) == 100:
                next_url = track_information['next']
                new_response = requests.get(next_url, headers=headers)
                playlist_data = new_response.json()
                tracklist.extend(playlist_data['items'])
    else:
        logging.error(f"Error: {response.status_code}, {playlist_data.get('error', {}).get('message')}")

    playlist_length = len(tracklist)
    all_tracks = [tracklist[i]['track']['id'] for i in range(playlist_length)]
    logging.info(f'  Number of tracks: {len(all_tracks)}')

    return all_tracks

def create_playlist(token : str,
                    user_id : str,
                    playlist_name : str) -> str:
    """Create a new empty playlist

    Parameters
    ----------
        token : str
            The access token for the Spotify API.
        user_id : str
            The user ID of the Spotify user.
        playlist_name : str
            The name of the playlist to create.

    Returns
    -------
        playlist_id : str
            The ID of the created playlist.
    """
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    data = {
        'name': playlist_name,
        'public': True,  # Set False to create a private playlist
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        playlist_id = response.json().get('id')
        logging.info(f"Playlist '{playlist_name}' created with ID: {playlist_id}")
        return playlist_id
    else:
        logging.error(f"Failed to create playlist. Status code: {response.status_code}")
        return None

def add_tracks_to_playlist(token : str,
                           playlist_id : str,
                           track_ids : str) -> None:
    """Add a list of track ids to a playlist.

    Parameters
    ----------
        token : str
            The access token for the Spotify API.
        playlist_id : str
            The ID of the playlist.
        track_ids : list
            A list of track IDs to add to the playlist.
    """
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    data = {
        'uris': [f'spotify:track:{track_id}' for track_id in track_ids],
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        logging.info(f"  {len(track_ids)} tracks added to playlist '{playlist_id}' successfully.")
    else:
        logging.error(f"Failed to add tracks to playlist. Status code: {response.status_code}")


def add_track_information(tracks : list) -> dict:
    """Add removed state and date added information to track id for json format output.

    Parameters
    ----------
        tracks : list
            A list of track IDs.

    Returns
    -------
        track_information : dict
            A dictionary of track IDs with removed state and date added information.
    """

    track_information = {f'{track}': {'removed': False,
                                      'date_added': datetime.date.today().strftime('%d %b %Y')
                                      } for track in tracks}

    return track_information


def save_tracks_to_json(playlist_name : str,
                        track_ids : list) -> None:
    """Save the track id list to a json file.

    Parameters
    ----------
        playlist_name : str
            The name of the playlist.
        track_ids : list
            A list of track IDs.
    """

    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')

    with open(file_path, 'w') as file:
        logging.info("Writing new JSON")
        json.dump(track_ids, file, indent = 0)

def read_tracks_from_json(playlist_name : str) -> dict or None:
    """Read track information from a local json.

    Parameters
    ----------
        playlist_name : str
            The name of the playlist.

    Returns
    -------
        saved_tracks : dict
            A dictionary of track IDs with removed state and date added information.
    """

    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')

    if os.path.exists(file_path):
        logging.info(f"Reading stored playlist information for {playlist_name}")
        with open(file_path, 'r') as file:
            saved_tracks = json.load(file)
        logging.info(f"  {len(saved_tracks)} tracks in {filename}.json")
        return saved_tracks
    else:
        logging.info("No existing JSON")


def update_tracks_json(playlist_name : str,
                       new_track_ids : list,
                       removed_track_ids : list,
                       create_backup : bool=True) -> None:
    """Update a JSON file with new and removed tracks for a given playlist.

    Parameters
    ----------
        playlist_name : str
            The name of the playlist.
        new_track_ids : list
            A list of track IDs to add to the playlist.
        removed_track_ids : list
            A list of track IDs to remove from the playlist.
        create_backup : bool
            Whether to create a backup of the existing JSON.
    """

    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}')

    if os.path.exists(file_path + '.json'):
        logging.info(f"Updating {filename}.json")
        with open(file_path + '.json', 'r') as file:
            existing_tracks = json.load(file)

        if create_backup:
            logging.info(f"  Creating backup for date: {datetime.date.today().strftime('%d %b %Y')}")
            with open(file_path + '-' + datetime.date.today().strftime('%d-%m-%Y') + '.json', 'w') as file:
                json.dump(existing_tracks, file, indent = 0)

        with open(file_path + '.json', 'w') as file:
            logging.info("  Removing removed tracks")
            logging.info(f"    {len(removed_track_ids)} tracks removed in total")
            for track in removed_track_ids:
                existing_tracks[track]['removed'] = True
            logging.info("  Adding new tracks")
            logging.info(f"    {len(new_track_ids)} tracks added")
            for track in new_track_ids:
                existing_tracks.update({f'{track}': {'removed': False, 'date_added': datetime.date.today().strftime('%d %b %Y')}})
            json.dump(existing_tracks, file, indent = 0)
    else:
        logging.info("No existing JSON")


def compare_tracklists(public_track_ids : list,
                       user_track_ids : list,
                       saved_tracks : dict) -> (list, list):
    """Compare the new public tracklist, the user's tracklist and the saved tracks to find changes.

    Parameters
    ----------
        public_track_ids : list
            A list of track IDs from the public playlist.
        user_track_ids : list
            A list of track IDs from the user's playlist.
        saved_tracks : dict
            A dictionary of track IDs with removed state and date added information.

    Returns
    -------
        new_tracks : list
    """

    saved_track_ids = list(saved_tracks.keys())
    unique_new_tracks = [track for track in public_track_ids if track not in user_track_ids]
    new_tracks = [track for track in unique_new_tracks if track not in saved_track_ids]
    removed_tracks = [track for track in saved_track_ids if track not in user_track_ids]

    return new_tracks, removed_tracks

