import os
import re
import requests
import logging
from flask import Flask, session, request, redirect, url_for, render_template, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Import our new direct API client and the database models
import spotify_client
from models import db, User, TrackedPlaylist

# --- Basic Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# --- Database Configuration ---
# Sets the database URI to a file named 'trackify.db' in the instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///trackify.db"
# Initialize the database with our app
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
    token = get_auth_token()
    if not token: return redirect(url_for('login'))
    
    sp = spotipy.Spotify(auth=token)
    user_info = sp.current_user()
    playlists = sp.current_user_playlists()
    return render_template('profile.html', user=user_info, playlists=playlists['items'])

@app.route('/playlist/<playlist_id>')
def playlist_detail(playlist_id):
    token = get_auth_token()
    if not token: return redirect(url_for('login'))
    
    try:
        sp = spotipy.Spotify(auth=token)
        market = sp.current_user().get('country')
        playlist_info = spotify_client.get_playlist_details(token, playlist_id, market=market)
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
        market = user_info.get('country')
        user_id = user_info.get('id')

        # --- Database Logic ---
        # 1. Find or create the user in our database
        user = db.session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            db.session.add(user)
            db.session.commit()

        # --- Spotify API Logic ---
        # 2. Get source playlist details
        source_playlist = spotify_client.get_playlist_details(token, source_playlist_id, market=market)
        source_playlist_name = source_playlist['name']

        # 3. Get all track URIs from the source playlist
        track_uris = spotify_client.get_all_track_uris(token, source_playlist, market=market)
        
        # 4. Create the new tracked playlist for the user
        new_playlist_name = f"{source_playlist_name} (Trackify)"
        description = f"Tracked version of '{source_playlist_name}'. Created by Trackify."
        new_playlist_id = spotify_client.create_new_playlist(token, user_id, new_playlist_name, description)

        # 5. Add tracks to the new playlist
        if track_uris:
            spotify_client.add_tracks_to_playlist(token, new_playlist_id, track_uris)
        
        # --- Database Logic ---
        # 6. Save the tracking information to our database
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

# This block creates the database file and tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=8888)
