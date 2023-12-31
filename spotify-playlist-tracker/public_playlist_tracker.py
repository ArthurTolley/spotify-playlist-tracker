from utils import *
import os
import subprocess

print("---")
token = get_access_token()
user_id = '1172837699' # My User ID (Arthur Tolley) - https://open.spotify.com/user/1172837699?si=01ce7bd378384e14
playlist_id = '37i9dQZF1DWY4lFlS4Pnso?si=8a3e6f1435694250' #Hot Hits UK - https://open.spotify.com/playlist/37i9dQZF1DWY4lFlS4Pnso?si=d767797688764421
user_playlist_name = 'Hot Hits UK Tracker'

script_directory = os.path.dirname(os.path.abspath(__file__))

# Query user playlists to see if the playlist already exists:
#  If so, update it
#  If not, create it
user_playlists = get_user_playlists(token, user_id)
if user_playlist_name in user_playlists['playlist_names']:
    print("")
    print(f"Playlist Name: '{user_playlist_name}' already exists in User's Playlists")
    print(f"  Updating: '{user_playlist_name}'")
    script_path = f'{script_directory}/update_playlist.py'
    script_arguments = [token, user_id, playlist_id, user_playlist_name]
    subprocess.run(['python', script_path] + script_arguments)
else:
    print(f"Creating new playlist called: {user_playlist_name}")
    script_path = f'{script_directory}/new_playlist.py'
    script_arguments = [token, user_id, playlist_id, user_playlist_name]
    subprocess.run(['python', script_path] + script_arguments)

