# Spotify Playlist Tracker

<p align="center">
  <img src="<temp>" alt="Spotify Playlist Tracker Banner" width="600"/>
</p>

<p align="center">
  <strong>Keep the hits, lose the misses.</strong>
</p>

---

This web application helps you manage and filter your favorite Spotify playlists. It allows you to "track" a source playlist, creating your own personal, filterable copy. When you remove a song you don't like from your version, the app remembers your choice and won't re-add it, even when the original playlist updates.

## ✨ Features

* **Playlist Tracking:** Create a personal, tracked copy of any public Spotify playlist.
* **Smart Sync:** Update your tracked playlist with new songs from the source playlist with a single click.
* **Dislike Memory:** Songs you remove from your tracked playlist are permanently remembered and ignored in future syncs.
* **Automated Weekly Syncs:** Set your playlists to update automatically every week.
* **Web-Based UI:** Manage your playlists through a simple, clean, and modern web interface.

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* A [Spotify Developer](https://developer.spotify.com/dashboard/) account and API credentials (Client ID & Client Secret).
* Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/spotify-playlist-tracker.git](https://github.com/your-username/spotify-playlist-tracker.git)
    cd spotify-playlist-tracker
    ```

2.  **Set up the Python Backend:**
    ```bash
    # Navigate to the backend directory
    cd backend

    # Create and activate a virtual environment
    # On macOS/Linux:
    python3 -m venv venv
    source venv/bin/activate

    # On Windows:
    python -m venv venv
    .\venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    * Create a `.env` file in the `backend/` directory by copying the example:
        ```bash
        cp .env.example .env
        ```
    * Open the `.env` file and add your Spotify API credentials. You also need to add your Redirect URI in your Spotify Developer Dashboard.
        ```
        SPOTIPY_CLIENT_ID="YOUR_SPOTIFY_CLIENT_ID"
        SPOTIPY_CLIENT_SECRET="YOUR_SPOTIFY_CLIENT_SECRET"
        SPOTIPY_REDIRECT_URI="[http://127.0.0.1:8888/callback](http://127.0.0.1:8888/callback)"
        FLASK_SECRET_KEY="A_RANDOM_SECRET_KEY_FOR_SESSIONS"
        ```

4.  **Run the application:**
    ```bash
    # From the backend directory
    flask run
    ```

5.  **Access the Frontend:**
    * Open `http://127.0.0.1:8888` in your web browser.

## 🛠️ Technology Stack

* **Backend:** Python, Flask
* **Spotify API Wrapper:** Spotipy
* **Database:** SQLAlchemy with SQLite
* **Scheduled Jobs:** APScheduler for automated weekly syncs
* **Frontend:** HTML, Tailwind CSS

## 🤝 Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](arthurtolley/spotify-playlist-tracker/spotify-playlist-tracker-ac49e65934a0de7d7a1a9cbff0ff584d6621d7e7/LICENSE) file for details.