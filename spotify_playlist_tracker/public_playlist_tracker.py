from utils import *
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

logging.info('Starting Public Playlist Tracker')
token = get_access_token()
user_id = '1172837699' # My User ID (Arthur Tolley) - https://open.spotify.com/user/1172837699
playlist_id = '37i9dQZF1DWY4lFlS4Pnso' #Hot Hits UK - https://open.spotify.com/playlist/37i9dQZF1DWY4lFlS4Pnso
user_playlist_name = 'Hot Hits UK Tracker'

script_directory = os.path.dirname(os.path.abspath(__file__))

# Query user playlists to see if the playlist already exists:
#  If so, update it
#  If not, create it
user_playlists = get_user_playlists(token, user_id)
if user_playlist_name in user_playlists['playlist_names']:
    # If the playlist exists then grab the ID
    index = user_playlists['playlist_names'].index(user_playlist_name)
    user_playlist_id = user_playlists['playlist_ids'][index]

    logging.info(f"Playlist: '{user_playlist_name}' already exists, updating with latest tracks.")
    script_path = f'{script_directory}/update_playlist.py'
    script_arguments = [token, user_id, playlist_id, user_playlist_name, user_playlist_id]
    subprocess.run(['python', script_path] + script_arguments)
else:
    logging.info(f"Creating new playlist: {user_playlist_name}")
    script_path = f'{script_directory}/new_playlist.py'
    script_arguments = [token, user_id, playlist_id, user_playlist_name]
    subprocess.run(['python', script_path] + script_arguments)

