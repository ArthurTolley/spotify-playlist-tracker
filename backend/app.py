import os
from flask import Flask, session, request, redirect, url_for, render_template, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask App
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")

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

# --- Helper Function to get Spotify client ---
def get_spotify_client():
    """Checks for a valid token and returns a Spotipy client instance."""
    if not sp_oauth.validate_token(CACHE_HANDLER.get_cached_token()):
        return None
    return spotipy.Spotify(auth_manager=sp_oauth)

# --- Routes ---
@app.route('/')
def index():
    """Redirects to profile if logged in, otherwise shows frontend link."""
    if get_spotify_client():
        return redirect(url_for('profile'))
    return '<h1>Welcome to Trackify!</h1><p>Please open the <strong>frontend/index.html</strong> file to log in.</p>'

@app.route('/login')
def login():
    """Redirects the user to Spotify's authorization page."""
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    """Handles the redirect from Spotify after authentication."""
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    flash("You have been successfully logged out.")
    return '<h1>Logged out!</h1><p>You can now close this tab or <a href="http://localhost:8888/login">log in again</a>.</p>'

@app.route('/profile')
def profile():
    """Displays the user's profile and their playlists."""
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))

    user_info = sp.current_user()
    playlists = sp.current_user_playlists()

    return render_template('profile.html', user=user_info, playlists=playlists['items'])

@app.route('/playlist/<playlist_id>')
def playlist_detail(playlist_id):
    """Shows the details and tracks of a specific playlist."""
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))

    try:
        # Fetch playlist details
        playlist_info = sp.playlist(playlist_id)

        # Fetch all tracks from the playlist
        results = sp.playlist_items(playlist_id)
        tracks = results['items']

        # Spotify API paginates results, so we need to get all pages
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

    except spotipy.exceptions.SpotifyException as e:
        flash(f"Could not retrieve playlist. Error: {e}")
        return redirect(url_for('profile'))

    return render_template('playlist_detail.html', playlist=playlist_info, tracks=tracks)


if __name__ == '__main__':
    app.run(debug=True, port=8888)
