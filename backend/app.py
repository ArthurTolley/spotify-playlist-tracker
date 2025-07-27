import os
import re
import requests
import logging
from flask import Flask, session, request, redirect, url_for, render_template, flash
from markupsafe import Markup # Import Markup from its new location
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Import our new direct API client and the database models
import spotify_client
from models import db, User, TrackedPlaylist, DislikedSong

# --- Basic Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# --- Database Configuration ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trackify.db"
db.init_app(app)

# --- Spotify OAuth Configuration ---
SCOPE = "playlist-modify-public playlist-read-private playlist-modify-private user-read-private"
CACHE_HANDLER = spotipy.cache_handler.FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=SCOPE,
    cache_handler=CACHE_HANDLER,
    show_dialog=True
)

# --- Helper Functions ---
def get_auth_token():
    """Retrieves the access token from the session cache."""
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        return None
    return token_info['access_token']

def parse_playlist_id(url_or_uri):
    """Parses a Spotify URL, URI, or ID to extract just the playlist ID."""
    match = re.search(r'playlist/([a-zA-Z0-9]{22})', url_or_uri)
    if match: return match.group(1)
    match = re.search(r':playlist:([a-zA-Z0-9]{22})', url_or_uri)
    if match: return match.group(1)
    if re.fullmatch(r'[a-zA-Z0-9]{22}', url_or_uri): return url_or_uri
    return None

# --- Routes ---
@app.route('/')
def index():
    if not get_auth_token():
        return '<h1>Welcome to Trackify!</h1><p>Please open the <strong>frontend/index.html</strong> file to log in.</p>'
    return redirect(url_for('profile'))

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.")
    return '<h1>Logged out!</h1><p>You can now close this tab or <a href="http://localhost:8888/login">log in again</a>.</p>'

@app.route('/profile')
def profile():
    """Displays user info, tracked playlists from DB, and all user playlists from Spotify."""
    token = get_auth_token()
    if not token: return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=token)
    user_info = sp.current_user()
    
    # Get all of the user's playlists from Spotify
    all_user_playlists = sp.current_user_playlists()
    
    # Get the playlists this user is tracking from our database
    tracked_playlists_from_db = db.session.execute(
        db.select(TrackedPlaylist).where(TrackedPlaylist.user_id == user_info['id'])
    ).scalars().all()

    # --- FIX: More reliable check for deleted playlists ---
    # Create a set of all actual playlist IDs for fast checking
    actual_playlist_ids = {p['id'] for p in all_user_playlists['items']}
    
    valid_tracked_playlists = []
    playlists_to_delete_from_db = []
    
    for tp in tracked_playlists_from_db:
        if tp.tracked_playlist_id in actual_playlist_ids:
            valid_tracked_playlists.append(tp)
        else:
            # This playlist is in our DB but not on Spotify, so it was deleted.
            logging.info(f"Tracked playlist '{tp.tracked_playlist_name}' (ID: {tp.tracked_playlist_id}) not found on Spotify. Deleting from DB.")
            playlists_to_delete_from_db.append(tp)
    
    # If we found any deleted playlists, remove them from our database
    if playlists_to_delete_from_db:
        for tp in playlists_to_delete_from_db:
            # Delete associated disliked songs first to maintain integrity
            db.session.execute(
                db.delete(DislikedSong).where(DislikedSong.tracked_playlist_id == tp.id)
            )
            # Then delete the tracked playlist record itself
            db.session.delete(tp)
        db.session.commit()
        flash(f"Removed {len(playlists_to_delete_from_db)} tracked playlist(s) that were deleted on Spotify.", 'info')

    return render_template(
        'profile.html', 
        user=user_info, 
        tracked_playlists=valid_tracked_playlists,  # Pass the cleaned list to the template
        playlists=all_user_playlists['items']
    )

@app.route('/playlist/<playlist_id>')
def playlist_detail(playlist_id):
    token = get_auth_token()
    if not token: return redirect(url_for('login'))
    
    try:
        playlist_info = spotify_client.get_playlist_details(token, playlist_id)
        tracks_for_template = playlist_info['tracks']['items']
    except requests.exceptions.HTTPError as e:
        flash(f"Could not retrieve playlist. Error: {e.response.status_code} - {e.response.text}", 'error')
        return redirect(url_for('profile'))
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", 'error')
        return redirect(url_for('profile'))

    return render_template('playlist_detail.html', playlist=playlist_info, tracks=tracks_for_template)

@app.route('/track', methods=['POST'])
def track():
    """Handles the logic for tracking a new playlist and saving it to the database."""
    token = get_auth_token()
    if not token: return redirect(url_for('login'))

    playlist_url = request.form.get('playlist_url')
    source_playlist_id = parse_playlist_id(playlist_url)

    if not source_playlist_id:
        flash("Could not find a valid Spotify ID in the link you provided.", 'error')
        return redirect(url_for('profile'))

    try:
        sp = spotipy.Spotify(auth=token)
        user_info = sp.current_user()
        user_id = user_info.get('id')

        # --- DB Check to prevent duplicates ---
        existing_tracking = db.session.execute(db.select(TrackedPlaylist).where(
            TrackedPlaylist.user_id == user_id,
            TrackedPlaylist.source_playlist_id == source_playlist_id
        )).scalar_one_or_none()

        if existing_tracking:
            flash("You are already tracking this playlist.", 'error')
            return redirect(url_for('profile'))

        # --- DB Logic: Find or create user ---
        user = db.session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            db.session.add(user)
            db.session.commit()

        # --- Spotify API Logic ---
        source_playlist = spotify_client.get_playlist_details(token, source_playlist_id)
        source_playlist_name = source_playlist['name']
        track_uris = spotify_client.get_all_track_uris(token, source_playlist)
        new_playlist_name = f"{source_playlist_name} (Trackify)"
        description = f"Tracked version of '{source_playlist_name}'. Created by Trackify."
        new_playlist_id = spotify_client.create_new_playlist(token, user_id, new_playlist_name, description)
        if track_uris:
            spotify_client.add_tracks_to_playlist(token, new_playlist_id, track_uris)
        
        # --- DB Logic: Save tracking info ---
        new_tracked_playlist = TrackedPlaylist(
            user_id=user_id,
            source_playlist_id=source_playlist_id,
            tracked_playlist_id=new_playlist_id,
            tracked_playlist_name=new_playlist_name
        )
        db.session.add(new_tracked_playlist)
        db.session.commit()
        
        flash(f"Successfully created and tracked '{new_playlist_name}'!", 'success')

    except requests.exceptions.HTTPError as e:
        flash(f"A Spotify API error occurred: {e.response.status_code} - {e.response.text}", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", 'error')

    return redirect(url_for('profile'))

@app.route('/sync/<int:tracked_playlist_db_id>', methods=['POST'])
def sync(tracked_playlist_db_id):
    """Compares a source and tracked playlist, adds new songs, and remembers dislikes."""
    token = get_auth_token()
    if not token: return redirect(url_for('login'))

    tracked_playlist = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not tracked_playlist:
        flash("Tracked playlist not found in database.", 'error')
        return redirect(url_for('profile'))

    sp = spotipy.Spotify(auth=token)
    user_info = sp.current_user()
    if tracked_playlist.user_id != user_info.get('id'):
        flash("You do not have permission to sync this playlist.", 'error')
        return redirect(url_for('profile'))
        
    try:
        # 1. Get all track URIs from source and user's tracked playlist
        source_data = spotify_client.get_playlist_details(token, tracked_playlist.source_playlist_id)
        source_uris = set(spotify_client.get_all_track_uris(token, source_data))

        tracked_data = spotify_client.get_playlist_details(token, tracked_playlist.tracked_playlist_id)
        tracked_uris = set(spotify_client.get_all_track_uris(token, tracked_data))

        # 2. Get previously disliked songs from our database
        disliked_songs = db.session.execute(db.select(DislikedSong).where(DislikedSong.tracked_playlist_id == tracked_playlist.id)).scalars().all()
        disliked_uris_db = {song.song_uri for song in disliked_songs}

        # 3. **FIX**: Find and record newly disliked songs FIRST
        potential_disliked = source_uris - tracked_uris
        newly_disliked_to_save = potential_disliked - disliked_uris_db

        if newly_disliked_to_save:
            for uri in newly_disliked_to_save:
                disliked_song = DislikedSong(song_uri=uri, tracked_playlist_id=tracked_playlist.id)
                db.session.add(disliked_song)
            db.session.commit()
            logging.info(f"Recorded {len(newly_disliked_to_save)} newly disliked songs.")
            # Update our in-memory set for the next step
            disliked_uris_db.update(newly_disliked_to_save)

        # 4. **FIX**: NOW find songs to add using the updated disliked list
        songs_to_add = list(source_uris - tracked_uris - disliked_uris_db)

        if songs_to_add:
            spotify_client.add_tracks_to_playlist(token, tracked_playlist.tracked_playlist_id, songs_to_add)
            flash(f"Sync complete! Added {len(songs_to_add)} new song(s).", 'success')
        else:
            flash("Sync complete! Your playlist is up to date.", 'success')

    except requests.exceptions.HTTPError as e:
        flash(f"A Spotify API error occurred during sync: {e.response.status_code} - {e.response.text}", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred during sync: {e}", 'error')

    return redirect(url_for('profile'))

@app.route('/untrack/<int:tracked_playlist_db_id>', methods=['POST'])
def untrack(tracked_playlist_db_id):
    """Removes a tracked playlist from the database."""
    token = get_auth_token()
    if not token: return redirect(url_for('login'))

    playlist_to_untrack = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not playlist_to_untrack:
        flash("Playlist not found in tracking database.", 'error')
        return redirect(url_for('profile'))
    
    # Store data in session for potential undo
    session['undo_data'] = {
        'user_id': playlist_to_untrack.user_id,
        'source_playlist_id': playlist_to_untrack.source_playlist_id,
        'tracked_playlist_id': playlist_to_untrack.tracked_playlist_id,
        'tracked_playlist_name': playlist_to_untrack.tracked_playlist_name,
    }
    
    # Delete associated disliked songs first
    db.session.execute(db.delete(DislikedSong).where(DislikedSong.tracked_playlist_id == playlist_to_untrack.id))
    db.session.delete(playlist_to_untrack)
    db.session.commit()

    # Create a flash message with an "Undo" link
    undo_url = url_for('undo_untrack')
    message = Markup(f"Successfully untracked '{playlist_to_untrack.tracked_playlist_name}'. <a href='{undo_url}' class='font-bold underline'>Undo</a>")
    flash(message, 'success')

    return redirect(url_for('profile'))

@app.route('/undo_untrack')
def undo_untrack():
    """Restores a recently untracked playlist from session data."""
    undo_data = session.pop('undo_data', None)

    if not undo_data:
        flash("No untrack action to undo.", 'error')
        return redirect(url_for('profile'))
    
    # Re-create the tracked playlist entry in the database
    restored_playlist = TrackedPlaylist(
        user_id=undo_data['user_id'],
        source_playlist_id=undo_data['source_playlist_id'],
        tracked_playlist_id=undo_data['tracked_playlist_id'],
        tracked_playlist_name=undo_data['tracked_playlist_name'],
    )
    db.session.add(restored_playlist)
    db.session.commit()

    flash(f"Restored tracking for '{restored_playlist.tracked_playlist_name}'.", 'success')
    return redirect(url_for('profile'))

@app.route('/delete/<int:tracked_playlist_db_id>', methods=['POST'])
def delete_playlist(tracked_playlist_db_id):
    """Deletes a tracked playlist from Spotify and the database."""
    token = get_auth_token()
    if not token: return redirect(url_for('login'))

    playlist_to_delete = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not playlist_to_delete:
        flash("Playlist not found in tracking database.", 'error')
        return redirect(url_for('profile'))

    sp = spotipy.Spotify(auth=token)
    user_info = sp.current_user()
    if playlist_to_delete.user_id != user_info.get('id'):
        flash("You do not have permission to delete this playlist.", 'error')
        return redirect(url_for('profile'))

    try:
        # 1. Delete from Spotify by unfollowing it
        sp.current_user_unfollow_playlist(playlist_to_delete.tracked_playlist_id)
        logging.info(f"Unfollowed (deleted) playlist {playlist_to_delete.tracked_playlist_id} from Spotify.")

        # 2. Delete from our database
        db.session.execute(db.delete(DislikedSong).where(DislikedSong.tracked_playlist_id == playlist_to_delete.id))
        db.session.delete(playlist_to_delete)
        db.session.commit()
        logging.info(f"Deleted playlist {playlist_to_delete.tracked_playlist_id} from local database.")

        flash(f"Successfully deleted '{playlist_to_delete.tracked_playlist_name}' from Spotify and untracked it.", 'success')
    except Exception as e:
        flash(f"An error occurred while deleting the playlist: {e}", 'error')

    return redirect(url_for('profile'))


# This block creates the database file and tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=8888)
