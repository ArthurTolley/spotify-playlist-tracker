from utils import *
import sys

token = sys.argv[1]
user_id = sys.argv[2]
playlist_id = sys.argv[3]
user_playlist_name = sys.argv[4]

# Create new playlist from Public Playlist
playlist_tracks = get_playlist_tracks(token, playlist_id)
playlist_id = create_playlist(token, user_id, user_playlist_name)
add_tracks_to_playlist(token, playlist_id, playlist_tracks)

# Save playlist tracks to JSON
track_information = add_track_information(playlist_tracks)
save_tracks_to_json(user_playlist_name, track_information)
