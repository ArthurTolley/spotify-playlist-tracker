from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey
from typing import List
from datetime import datetime

# --- Database Setup ---
# This setup allows us to define our models in a separate file.
# We will initialize the 'db' object with our Flask app in app.py.

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

# --- Model Definitions ---

class User(db.Model):
    """Represents a user of the application."""
    __tablename__ = 'user'

    # The user's Spotify ID will be our primary key
    id: Mapped[str] = mapped_column(String, primary_key=True)
    refresh_token: Mapped[str | None] = mapped_column(String)

    # Establishes a one-to-many relationship with TrackedPlaylist
    #  A user can have many tracked playlists.
    tracked_playlists: Mapped[List["TrackedPlaylist"]] = relationship(back_populates="user")

class TrackedPlaylist(db.Model):
    """Represents a playlist that a user is tracking."""
    __tablename__ = 'tracked_playlist'

    id: Mapped[int] = mapped_column(primary_key=True)

    # The ID of the original playlist on Spotify (e.g., the public chart)
    source_playlist_id: Mapped[str] = mapped_column(String, nullable=False)

    # The ID of the new playlist created in the user's account
    tracked_playlist_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    # The name of the playlist we created
    tracked_playlist_name: Mapped[str] = mapped_column(String, nullable=False)

    # The timestamp of the last successful sync
    last_synced: Mapped[datetime | None] = mapped_column(nullable=True)

    auto_sync_enabled: Mapped[bool] = mapped_column(default=False)
    job_id: Mapped[str | None] = mapped_column(String)

    # Foreign key to link back to the user who owns this tracked playlist
    user_id: Mapped[str] = mapped_column(ForeignKey("user.id"))

    # Establishes the other side of the one-to-many relationship
    user: Mapped["User"] = relationship(back_populates="tracked_playlists")

    # A tracked playlist can have many disliked songs
    disliked_songs: Mapped[List["DislikedSong"]] = relationship(cascade="all, delete-orphan")

class DislikedSong(db.Model):
    """Represents a song a user has removed from a tracked playlist."""
    __tablename__ = 'disliked_song'

    id: Mapped[int] = mapped_column(primary_key=True)

    # The Spotify URI of the song (e.g., 'spotify:track:12345')
    song_uri: Mapped[str] = mapped_column(String, nullable=False)

    # Foreign key to link back to the specific tracked playlist
    tracked_playlist_id: Mapped[int] = mapped_column(ForeignKey("tracked_playlist.id"))