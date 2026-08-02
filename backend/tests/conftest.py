import os
import sys
import tempfile
from pathlib import Path

# Make the backend directory importable regardless of where pytest is invoked from
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set environment variables BEFORE importing the app so it boots against a
# throwaway SQLite database and dummy Spotify credentials (no live Postgres).
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["SPOTIPY_CLIENT_ID"] = "test_client_id"
os.environ["SPOTIPY_CLIENT_SECRET"] = "test_client_secret"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost/callback"
os.environ["FLASK_SECRET_KEY"] = "test_secret_key"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

import pytest  # noqa: E402

# Importing the app triggers db.create_all() and scheduler.start();
# the scheduler is harmless to keep running in tests.
from app import app, db, scheduler  # noqa: E402, F401


@pytest.fixture()
def client():
    """Flask test client with a freshly recreated database per test."""
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()
