# Trackify Spotify Playlist Tracker

Trackify is a web application that helps you manage and filter your favorite Spotify playlists. It allows you to "track" a source playlist (like the UK Top 100) and maintain your own version. If you remove a song you don't like from your version, Trackify remembers your choice and won't re-add it, even when the original playlist updates.

## ✨ Features

* **Playlist Tracking:** Create a personal, tracked copy of any public Spotify playlist.
* **Smart Sync:** Update your tracked playlist with new songs from the source playlist.
* **Dislike Memory:** Songs you remove from your tracked playlist are permanently ignored in future syncs.
* **Web-Based UI:** Manage your playlists through a simple web interface.
* **(Planned) Automated Weekly Syncs:** Set your playlists to update automatically every week.

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* A Spotify Developer account and API credentials (Client ID & Client Secret).
* Git

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/trackify.git](https://github.com/your-username/trackify.git)
   cd trackify
   ```

2. **Set up the Python Backend:**
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

3. **Configure Environment Variables:**
   - Create a `.env` file in the `backend/` directory by copying the example:
     ```bash
     cp .env.example .env
     ```
   - Open the `.env` file and add your Spotify API credentials:
     ```
     SPOTIFY_CLIENT_ID='YOUR_SPOTIFY_CLIENT_ID'
     SPOTIFY_CLIENT_SECRET='YOUR_SPOTIFY_CLIENT_SECRET'
     FLASK_SECRET_KEY='A_RANDOM_SECRET_KEY_FOR_SESSIONS'
     # You will also need to add your Redirect URI here from the Spotify Dev Dashboard
     SPOTIFY_REDIRECT_URI='[http://127.0.0.1:5000/callback](http://127.0.0.1:5000/callback)'
     ```

4. **Run the application:**
   ```bash
   # From the backend directory
   flask run
   ```

5. **Access the Frontend:**
   - Open the `frontend/index.html` file in your web browser.

## Usage

1. Navigate to the web application.
2. Click "Login with Spotify" and authorize the application.
3. Paste the URL of a Spotify playlist you want to track and click "Track Playlist".
4. To update the playlist with new songs, click the "Sync" button.

---