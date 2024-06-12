Track public playlists.

Features:
- Update user playlist with new additions to the public playlist
- Remember removed tracks to prevent re-adding disliked tracks
- Produces a new playlist or updates a current playlist

Wants:
- Also maintains a master playlist of all added songs
- Convert to a web app
- Get somebody else to use and test to see if it works!

---
This is very very barebones right now. To run this program you must have a `.env` file which contains a SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET string of the form:
```
SPOTIPY_CLIENT_ID='string_taken_from_spotify'
SPOTIPY_CLIENT_SECRET='string_taken_from_spotify'
```
Once this has been created in the `spotify_playlist_tracker` directory you can then update `user_id`, `playlist_id` and `user_playlist_name` in `public_playlist_tracker.py`, then run `public_playlist_tracker.py` in a command line environment. This should create and update a playlist belonging to your user.

Step-by-step:
- Create `.env` file with SPOTIPY credentials in `spotify_playlist_tracker`
- Change `user_id`, `playlist_id` and `user_playlist_name` in `public_playlist_tracker.py`
- Run `public_playlist_tracker.py`

---
Getting Spotify credentials to use in the `.env`: https://developer.spotify.com/documentation/web-api/concepts/apps