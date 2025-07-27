import os
import re
import requests
import logging
from flask import Flask, session, request, redirect, url_for, render_template, flash
from markupsafe import Markup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from datetime import datetime
from flask_apscheduler import APScheduler
import spotify_client
from models import db, User, TrackedPlaylist, DislikedSong

# --- Basic Configuration ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Flask App Initialization ---
app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# --- Database Configuration ---
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///trackify.db")
db.init_app(app)

# --- Scheduler Configuration ---
scheduler = APScheduler()

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
    if match:
        return match.group(1)
    match = re.search(r':playlist:([a-zA-Z0-9]{22})', url_or_uri)
    if match:
        return match.group(1)
    if re.fullmatch(r'[a-zA-Z0-9]{22}', url_or_uri):
        return url_or_uri
    return None

# --- Background Job Definition ---
def run_sync_job(tracked_playlist_db_id):
    """The function that the scheduler will run in the background."""
    with app.app_context():
        logging.info(f"Running auto-sync for playlist ID: {tracked_playlist_db_id}")
        tracked_playlist = db.session.get(TrackedPlaylist, tracked_playlist_db_id)

        if not tracked_playlist or not tracked_playlist.auto_sync_enabled:
            logging.warning(f"Job fired for playlist {tracked_playlist_db_id}, but auto-sync is disabled. Stopping.")
            return

        user = db.session.get(User, tracked_playlist.user_id)
        if not user or not user.refresh_token:
            logging.error(f"Cannot sync: User {tracked_playlist.user_id} not found or has no refresh token.")
            return

        try:
            # Get a new access token using the refresh token
            new_token_info = sp_oauth.refresh_access_token(user.refresh_token)

            # Since we got a new token, save the new refresh token if one was returned
            if 'refresh_token' in new_token_info:
                user.refresh_token = new_token_info['refresh_token']
                db.session.commit()

            token = new_token_info['access_token']

            # --- Perform the sync logic (copied and adapted from /sync route) ---
            source_data = spotify_client.get_playlist_details(token, tracked_playlist.source_playlist_id)
            source_uris = set(spotify_client.get_all_track_uris(token, source_data))

            tracked_data = spotify_client.get_playlist_details(token, tracked_playlist.tracked_playlist_id)
            tracked_uris = set(spotify_client.get_all_track_uris(token, tracked_data))

            disliked_songs = db.session.execute(db.select(DislikedSong).where(DislikedSong.tracked_playlist_id == tracked_playlist.id)).scalars().all()
            disliked_uris_db = {song.song_uri for song in disliked_songs}

            songs_to_add = list(source_uris - tracked_uris - disliked_uris_db)

            if songs_to_add:
                spotify_client.add_tracks_to_playlist(token, tracked_playlist.tracked_playlist_id, songs_to_add)
                logging.info(f"Auto-sync for '{tracked_playlist.tracked_playlist_name}' added {len(songs_to_add)} songs.")
            else:
                logging.info(f"Auto-sync for '{tracked_playlist.tracked_playlist_name}' complete. No new songs.")

            tracked_playlist.last_synced = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logging.error(f"Auto-sync job failed for playlist {tracked_playlist_db_id}: {e}")


# --- Routes ---
@app.route('/')
def index():
    if get_auth_token():
        return redirect(url_for('profile'))

    # This correctly renders your template from the 'backend/templates' folder
    return render_template('index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'])

    # Save the refresh token to the database
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()
    user = db.session.get(User, user_info['id'])
    if not user:
        user = User(id=user_info['id'])
        db.session.add(user)

    user.refresh_token = token_info['refresh_token']
    db.session.commit()

    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.")
    return '<h1>Logged out!</h1><p>You can now close this tab or <a href="http://localhost:8888/login">log in again</a>.</p>'

@app.route('/profile')
def profile():
    token = get_auth_token()
    if not token:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token)
    user_info = sp.current_user()

    all_user_playlists_response = sp.current_user_playlists(limit=50)
    all_user_playlists = all_user_playlists_response['items']

    spotify_playlists_by_id = {p['id']: p for p in all_user_playlists}

    tracked_playlists_from_db = db.session.execute(
        db.select(TrackedPlaylist).where(TrackedPlaylist.user_id == user_info['id'])
    ).scalars().all()

    actual_playlist_ids = {p['id'] for p in all_user_playlists}

    valid_tracked_playlists = []
    playlists_to_delete_from_db = []

    for tp in tracked_playlists_from_db:
        if tp.tracked_playlist_id in actual_playlist_ids:
            playlist_details = spotify_playlists_by_id.get(tp.tracked_playlist_id)
            if playlist_details and playlist_details.get('images'):
                tp.cover_image_url = playlist_details['images'][0]['url']
            else:
                tp.cover_image_url = None

            if tp.last_synced:
                tp.last_synced_formatted = tp.last_synced.strftime('%Y-%m-%d %H:%M')
            else:
                tp.last_synced_formatted = 'Never'

            valid_tracked_playlists.append(tp)
        else:
            logging.info(f"Tracked playlist '{tp.tracked_playlist_name}' (ID: {tp.tracked_playlist_id}) not found on Spotify. Deleting from DB.")
            playlists_to_delete_from_db.append(tp)

    if playlists_to_delete_from_db:
        for tp in playlists_to_delete_from_db:
            if tp.job_id:
                try:
                    scheduler.remove_job(tp.job_id)
                except Exception as e:
                    logging.warning(f"Could not remove job {tp.job_id} for deleted playlist: {e}")
            db.session.execute(
                db.delete(DislikedSong).where(DislikedSong.tracked_playlist_id == tp.id)
            )
            db.session.delete(tp)
        db.session.commit()
        flash(f"Removed {len(playlists_to_delete_from_db)} tracked playlist(s) that were deleted on Spotify.", 'info')

    tracked_source_ids = {tp.source_playlist_id for tp in valid_tracked_playlists}
    tracked_playlist_ids = {tp.tracked_playlist_id for tp in valid_tracked_playlists}

    source_playlists = []
    for playlist_id in tracked_source_ids:
        if playlist_id in spotify_playlists_by_id:
            source_playlists.append(spotify_playlists_by_id[playlist_id])
        else:
            try:
                playlist_data = sp.playlist(playlist_id)
                source_playlists.append(playlist_data)
            except Exception as e:
                logging.error(f"Could not fetch source playlist {playlist_id}: {e}")

    return render_template(
        'profile.html',
        user=user_info,
        tracked_playlists=valid_tracked_playlists,
        all_user_playlists=all_user_playlists,
        source_playlists=source_playlists,
        tracked_source_ids=tracked_source_ids,
        tracked_playlist_ids=tracked_playlist_ids
    )

@app.route('/track', methods=['POST'])
def track():
    token = get_auth_token()
    if not token:
        return redirect(url_for('login'))

    playlist_url = request.form.get('playlist_url')
    custom_name = request.form.get('custom_name', '').strip()
    source_playlist_id = parse_playlist_id(playlist_url)

    if not source_playlist_id:
        flash("Could not find a valid Spotify ID in the link you provided.", 'error')
        return redirect(url_for('profile'))

    try:
        sp = spotipy.Spotify(auth=token)
        user_info = sp.current_user()
        user_id = user_info.get('id')

        existing_tracking = db.session.execute(db.select(TrackedPlaylist).where(
            TrackedPlaylist.user_id == user_id,
            TrackedPlaylist.source_playlist_id == source_playlist_id
        )).scalar_one_or_none()

        if existing_tracking:
            flash("You are already tracking this playlist.", 'error')
            return redirect(url_for('profile'))

        user = db.session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            db.session.add(user)
            db.session.commit()

        source_playlist = spotify_client.get_playlist_details(token, source_playlist_id)
        source_playlist_name = source_playlist['name']
        track_uris = spotify_client.get_all_track_uris(token, source_playlist)

        if custom_name:
            new_playlist_name = custom_name
        else:
            new_playlist_name = f"{source_playlist_name} (Trackify)"

        description = f"Tracked version of '{source_playlist_name}'. Created by Trackify."
        new_playlist_id = spotify_client.create_new_playlist(token, user_id, new_playlist_name, description)
        if track_uris:
            spotify_client.add_tracks_to_playlist(token, new_playlist_id, track_uris)

        new_tracked_playlist = TrackedPlaylist(
            user_id=user_id,
            source_playlist_id=source_playlist_id,
            tracked_playlist_id=new_playlist_id,
            tracked_playlist_name=new_playlist_name,
            last_synced=datetime.utcnow()
        )
        db.session.add(new_tracked_playlist)
        db.session.commit()

        flash(f"Successfully created and tracked '{new_playlist_name}'!", 'success')

    except requests.exceptions.HTTPError as e:
        flash(f"A Spotify API error occurred: {e.response.status_code}. Please try again later.", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", 'error')

    return redirect(url_for('profile'))

@app.route('/sync/<int:tracked_playlist_db_id>', methods=['POST'])
def sync(tracked_playlist_db_id):
    token = get_auth_token()
    if not token:
        return redirect(url_for('login'))

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
        source_data = spotify_client.get_playlist_details(token, tracked_playlist.source_playlist_id)
        source_uris = set(spotify_client.get_all_track_uris(token, source_data))
        tracked_data = spotify_client.get_playlist_details(token, tracked_playlist.tracked_playlist_id)
        tracked_uris = set(spotify_client.get_all_track_uris(token, tracked_data))
        disliked_songs = db.session.execute(db.select(DislikedSong).where(DislikedSong.tracked_playlist_id == tracked_playlist.id)).scalars().all()
        disliked_uris_db = {song.song_uri for song in disliked_songs}
        potential_disliked = source_uris - tracked_uris
        newly_disliked_to_save = potential_disliked - disliked_uris_db

        if newly_disliked_to_save:
            for uri in newly_disliked_to_save:
                disliked_song = DislikedSong(song_uri=uri, tracked_playlist_id=tracked_playlist.id)
                db.session.add(disliked_song)
            db.session.commit()
            logging.info(f"Recorded {len(newly_disliked_to_save)} newly disliked songs.")
            disliked_uris_db.update(newly_disliked_to_save)

        songs_to_add = list(source_uris - tracked_uris - disliked_uris_db)

        if songs_to_add:
            spotify_client.add_tracks_to_playlist(token, tracked_playlist.tracked_playlist_id, songs_to_add)
            flash(f"Sync complete! Added {len(songs_to_add)} new song(s).", 'success')
        else:
            flash("Sync complete! Your playlist is up to date.", 'success')

        tracked_playlist.last_synced = datetime.utcnow()
        db.session.commit()

    except requests.exceptions.HTTPError as e:
        flash(f"A Spotify API error occurred during sync: {e.response.status_code} - {e.response.text}", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred during sync: {e}", 'error')

    return redirect(url_for('profile'))

@app.route('/toggle_auto_sync/<int:tracked_playlist_db_id>', methods=['POST'])
def toggle_auto_sync(tracked_playlist_db_id):
    if not get_auth_token():
        return redirect(url_for('login'))

    tracked_playlist = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not tracked_playlist:
        flash("Playlist not found.", "error")
        return redirect(url_for('profile'))

    tracked_playlist.auto_sync_enabled = not tracked_playlist.auto_sync_enabled

    if tracked_playlist.auto_sync_enabled:
        job = scheduler.add_job(
            id=f'sync_{tracked_playlist.id}',
            func=run_sync_job,
            args=[tracked_playlist.id],
            trigger='interval',
            weeks=1,
            replace_existing=True
        )
        tracked_playlist.job_id = job.id
    else:
        if tracked_playlist.job_id:
            try:
                scheduler.remove_job(tracked_playlist.job_id)
            except Exception as e:
                logging.warning(f"Could not remove job {tracked_playlist.job_id}: {e}")
        tracked_playlist.job_id = None

    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/untrack/<int:tracked_playlist_db_id>', methods=['POST'])
def untrack(tracked_playlist_db_id):
    if not get_auth_token():
        return redirect(url_for('login'))

    playlist_to_untrack = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not playlist_to_untrack:
        flash("Playlist not found in tracking database.", 'error')
        return redirect(url_for('profile'))

    if playlist_to_untrack.job_id:
        try:
            scheduler.remove_job(playlist_to_untrack.job_id)
        except Exception as e:
            logging.warning(f"Could not remove job {playlist_to_untrack.job_id} during untrack: {e}")

    session['undo_data'] = {
        'user_id': playlist_to_untrack.user_id,
        'source_playlist_id': playlist_to_untrack.source_playlist_id,
        'tracked_playlist_id': playlist_to_untrack.tracked_playlist_id,
        'tracked_playlist_name': playlist_to_untrack.tracked_playlist_name,
    }

    db.session.execute(db.delete(DislikedSong).where(DislikedSong.tracked_playlist_id == playlist_to_untrack.id))
    db.session.delete(playlist_to_untrack)
    db.session.commit()

    undo_url = url_for('undo_untrack')
    message = Markup(f"Successfully untracked '{playlist_to_untrack.tracked_playlist_name}'. <a href='{undo_url}' class='font-bold underline'>Undo</a>")
    flash(message, 'success')

    return redirect(url_for('profile'))

@app.route('/undo_untrack')
def undo_untrack():
    undo_data = session.pop('undo_data', None)

    if not undo_data:
        flash("No untrack action to undo.", 'error')
        return redirect(url_for('profile'))

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
    if not get_auth_token():
        return redirect(url_for('login'))

    playlist_to_delete = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not playlist_to_delete:
        flash("Playlist not found in tracking database.", 'error')
        return redirect(url_for('profile'))

    sp = spotipy.Spotify(auth=get_auth_token())
    user_info = sp.current_user()
    if playlist_to_delete.user_id != user_info.get('id'):
        flash("You do not have permission to delete this playlist.", 'error')
        return redirect(url_for('profile'))

    try:
        if playlist_to_delete.job_id:
            try:
                scheduler.remove_job(playlist_to_delete.job_id)
            except Exception as e:
                logging.warning(f"Could not remove job {playlist_to_delete.job_id} during delete: {e}")

        sp.current_user_unfollow_playlist(playlist_to_delete.tracked_playlist_id)
        logging.info(f"Unfollowed (deleted) playlist {playlist_to_delete.tracked_playlist_id} from Spotify.")

        db.session.execute(db.delete(DislikedSong).where(DislikedSong.tracked_playlist_id == playlist_to_delete.id))
        db.session.delete(playlist_to_delete)
        db.session.commit()
        logging.info(f"Deleted playlist {playlist_to_delete.tracked_playlist_id} from local database.")

        flash(f"Successfully deleted '{playlist_to_delete.tracked_playlist_name}' from Spotify and untracked it.", 'success')
    except Exception as e:
        flash(f"An error occurred while deleting the playlist: {e}", 'error')

    return redirect(url_for('profile'))

@app.route('/edit_playlist/<int:tracked_playlist_db_id>')
def edit_playlist(tracked_playlist_db_id):
    token = get_auth_token()
    if not token:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token)

    tracked_playlist = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not tracked_playlist:
        flash("Playlist not found in tracking database.", 'error')
        return redirect(url_for('profile'))

    try:
        playlist_data = sp.playlist(tracked_playlist.tracked_playlist_id)
        playlist_data['db_id'] = tracked_playlist_db_id

    except Exception as e:
        flash(f"Could not load playlist from Spotify: {e}", 'error')
        return redirect(url_for('profile'))

    return render_template(
        'edit_playlist.html',
        playlist=playlist_data,
        tracks=playlist_data['tracks']['items']
    )

@app.route('/dislike_song/<int:tracked_playlist_db_id>/<track_uri>', methods=['POST'])
def dislike_song(tracked_playlist_db_id, track_uri):
    token = get_auth_token()
    if not token:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token)

    tracked_playlist = db.session.get(TrackedPlaylist, tracked_playlist_db_id)
    if not tracked_playlist:
        flash("Tracked playlist not found.", "error")
        return redirect(url_for('profile'))

    try:
        existing_dislike = db.session.execute(db.select(DislikedSong).where(
            DislikedSong.tracked_playlist_id == tracked_playlist_db_id,
            DislikedSong.song_uri == track_uri
        )).scalar_one_or_none()

        if not existing_dislike:
            new_dislike = DislikedSong(song_uri=track_uri, tracked_playlist_id=tracked_playlist_db_id)
            db.session.add(new_dislike)
            db.session.commit()
            logging.info(f"Added {track_uri} to disliked songs for playlist {tracked_playlist_db_id}")

        track_info = sp.track(track_uri.split(':')[-1])
        track_name = track_info['name']
        sp.playlist_remove_all_occurrences_of_items(tracked_playlist.tracked_playlist_id, [track_uri])

        flash(f"Successfully removed '{track_name}' and will prevent it from being added back.", "success")

    except Exception as e:
        flash(f"An error occurred: {e}", "error")

    return redirect(url_for('edit_playlist', tracked_playlist_db_id=tracked_playlist_db_id))

# Create the database file and tables if they don't exist
with app.app_context():
    db.create_all()

# Initialize and start the scheduler
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    # use_reloader=False is important for APScheduler to avoid running jobs twice
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, port=8888, use_reloader=False)