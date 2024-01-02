import os
import sys
import requests
import json
import datetime

from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

def get_access_token():
    """Create an access token to access the Spotofy API."""

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

    return token

def get_user_playlists(token, user_id):
    """Fetch the playlists of a user."""

    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        playlists_data = response.json()['items']
        num_playlists = len(response.json()['items'])
        playlist_names = [playlists_data[i]['name'] for i in range(num_playlists)]
        playlist_ids = [playlists_data[i]['id'] for i in range(num_playlists)]
        return {'playlist_names' : playlist_names,
                'playlist_ids' : playlist_ids}
    else:
        print(f"Failed to retrieve playlist names. Status code: {response.status_code}")
        return None

def get_playlist_tracks(token, playlist_id):
    """Fetch the track ids for a specific playlist id."""

    playlist_url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(playlist_url, headers=headers)
    playlist_data = response.json()

    if response.status_code == 200:
        playlist_name = playlist_data['name']
        owner_name = playlist_data['owner']['display_name']
        track_information = playlist_data['tracks']
        print("")
        print(f"Reading playlist: {playlist_name} by {owner_name}")

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
        # Handle errors
        print(f"Error: {response.status_code}, {playlist_data.get('error', {}).get('message')}")

    playlist_length = len(tracklist)
    all_tracks = [tracklist[i]['track']['id'] for i in range(playlist_length)]
    print(f'  Number of tracks: {len(all_tracks)}')

    return all_tracks

def create_playlist(token, user_id, playlist_name):
    """Create a new empty playlist """
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    data = {
        'name': playlist_name,
        'public': True,  # Set to True if you want the playlist to be public
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        playlist_id = response.json().get('id')
        print("")
        print(f"Playlist '{playlist_name}' created with ID: {playlist_id}")
        return playlist_id
    else:
        print(f"Failed to create playlist. Status code: {response.status_code}")
        return None

def add_tracks_to_playlist(token, playlist_id, track_ids):
    """Add a list of track ids to a playlist."""
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
        print(f"  {len(track_ids)} tracks added to playlist '{playlist_id}' successfully.")
    else:
        print(f"Failed to add tracks to playlist. Status code: {response.status_code}")


def add_track_information(tracks):
    """Add removed state and date added information to track id for json format output."""

    track_information = {f'{track}': {'removed': False,
                                      'date_added': datetime.date.today().strftime('%d %b %Y')
                                      } for track in tracks}

    return track_information


def save_tracks_to_json(playlist_name, playlist_tracks):
    """Save the track id list to a json file."""

    print("")
    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')

    with open(file_path, 'w') as file:
        print("Writing new JSON")
        json.dump(playlist_tracks, file, indent = 0)

def read_tracks_from_json(playlist_name):
    """Read track information from a local json."""

    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')

    if os.path.exists(file_path):
        print("")
        print("Reading existing JSON")
        with open(file_path, 'r') as file:
            existing_tracks = json.load(file)
        print(f"  {len(existing_tracks)} tracks in JSON")
        return existing_tracks
    else:
        print("No existing JSON")


def update_tracks_json(playlist_name, new_tracks, removed_tracks):
    """Update a json and create a backup for today."""

    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}')

    if os.path.exists(file_path + '.json'):
        print("")
        print("Updating existing JSON")
        with open(file_path + '.json', 'r') as file:
            existing_tracks = json.load(file)

        print(f"  Creating backup for date: {datetime.date.today().strftime('%d %b %Y')}")
        with open(file_path + '-' + datetime.date.today().strftime('%d-%m-%Y') + '.json', 'w') as file:
            json.dump(existing_tracks, file, indent = 0)

        with open(file_path + '.json', 'w') as file:
            print("  Removing removed tracks")
            print(f"    {len(removed_tracks)} tracks removed in total")
            for track in removed_tracks:
                existing_tracks[track]['removed'] = True
            print("  Adding new tracks")
            print(f"    {len(new_tracks)} tracks added")
            for track in new_tracks:
                existing_tracks.update({f'{track}': {'removed': False, 'date_added': datetime.date.today().strftime('%d %b %Y')}})
            json.dump(existing_tracks, file, indent = 0)
            print("Done!")
    else:
        print("No existing JSON")


def compare_tracklists(public_tracklist, user_tracklist, user_JSON):
    """Compare the new public tracklist, the user's tracklist and the existing json to find changes."""

    JSON_track_ids = list(user_JSON.keys())
    unique_new_tracks = [track for track in public_tracklist if track not in user_tracklist]
    new_tracks = [track for track in unique_new_tracks if track not in JSON_track_ids]
    removed_tracks = [track for track in JSON_track_ids if track not in user_tracklist]

    return new_tracks, removed_tracks

