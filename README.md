# Spotify Playlist Tracker

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
* **Runs anywhere:** single-command Docker Compose for local, Kubernetes for production.

## 🌐 Deployment Options

### Option 1: Production Deployment (Kubernetes + GitHub Pages)

**Frontend**: GitHub Pages (static landing page)  
**Backend**: Kubernetes cluster with Cloudflare Tunnel  
**Database**: PostgreSQL on Kubernetes  

See **[k8s/README.md](k8s/README.md)** for the complete deployment guide.

Quick links:
- [Kubernetes Setup](k8s/README.md)
- [Cloudflare Tunnel Setup](k8s/README.md)
- [Frontend Deployment](frontend/README.md)

### Option 2: Local Development (Docker Compose)

Perfect for testing and development. Runs the backend (Flask/Gunicorn + PostgreSQL), the database (Postgres 16 in the `db` service, auto-restored from `spotify_tracker.dump` on first boot), and the frontend (Nginx static site) in containers with a single command — no Python environment needed.

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine (no Python install required).
* A [Spotify Developer](https://developer.spotify.com/dashboard/) account and API credentials (Client ID & Client Secret).
* Git
* A `spotify_tracker.dump` (pg_dump custom format) file at the repo root is required before the first `docker compose up`; the `db` service restores it automatically on first boot. If the db service fails to start, place the dump and run `docker compose down -v && docker compose up --build`.

> **Note for Linux hosts:** the dump file may need `chmod 644 spotify_tracker.dump` so the postgres container can read it.

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/spotify-playlist-tracker.git
    cd spotify-playlist-tracker
    ```

2.  **Configure environment variables:**
    ```bash
    cp .env.example .env
    ```
    Open the `.env` file and fill in your Spotify API credentials:
    ```
    SPOTIPY_CLIENT_ID="YOUR_SPOTIFY_CLIENT_ID"
    SPOTIPY_CLIENT_SECRET="YOUR_SPOTIFY_CLIENT_SECRET"
    ```
    (The redirect URI, CORS origins, and database URL are pre-configured for local Docker Compose runs — no need to change them.)

3.  **Add the redirect URI to your Spotify app:**
    In the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/), add `http://127.0.0.1:8888/callback` to your app's Redirect URIs.

4.  **Run the application:**
    ```bash
    docker compose up --build
    # or: make run
    ```

5.  **Access the app:**
    Open `http://127.0.0.1:8888` in your web browser.

### Useful Commands

* `make logs` — stream backend and frontend logs
* `make stop` — stop the containers
* `make down` — stop and remove the containers (your Postgres data persists in the `postgres-data` Docker volume; `docker compose down -v` wipes it and the `/data` secret, requiring re-login)
* Verify the database was restored:
  ```bash
  docker compose exec db psql -U spotifytracker -d spotify_tracker -c '\dt'
  ```
* Re-restore from the dump (destructive — wipes the database):
  ```bash
  docker compose down -v && docker compose up --build
  ```

## 🛠️ Technology Stack

* **Backend:** Python, Flask, Gunicorn
* **Frontend:** HTML, Tailwind CSS, GitHub Pages
* **Spotify API Wrapper:** Spotipy
* **Database:** PostgreSQL
* **Scheduled Jobs:** APScheduler for automated weekly syncs
* **Deployment:** Docker, Kubernetes, Cloudflare Tunnel
* **CI/CD:** GitHub Actions

## 🤝 Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.