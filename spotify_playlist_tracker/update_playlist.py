from utils import *
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

token = sys.argv[1]
user_id = sys.argv[2]
playlist_id = sys.argv[3]
user_playlist_name = sys.argv[4]
user_playlist_id = sys.argv[5]

# Load in the JSON
existing_json = read_tracks_from_json(user_playlist_name)

# Load in the User Playlist
user_playlist_tracks = get_playlist_tracks(token, user_playlist_id)

# Load in the Spotify Playlist
public_playlist_tracks = get_playlist_tracks(token, playlist_id)

# If the JSON doesn't exist then make one
if not existing_json:
    track_information = add_track_information(user_playlist_tracks)
    save_tracks_to_json(user_playlist_name, track_information)

# Compare differences between tracks in user playlist and public playlist
new_tracks, removed_tracks = compare_tracklists(public_playlist_tracks,
                                                user_playlist_tracks,
                                                user_JSON=existing_json)

# Update the JSON, saving out a copy of the previous one
update_tracks_json(playlist_name=user_playlist_name,
                   new_track_ids=new_tracks,
                   removed_track_ids=removed_tracks,
                   create_backup=True)

# Add new track to playlist
if len(new_tracks) > 0:
    logging.info(f"  Adding {len(new_tracks)} tracks to user playlist")
    add_tracks_to_playlist(token, user_playlist_id, new_tracks)
else:
    logging.info("No new track to add, end of program.")
