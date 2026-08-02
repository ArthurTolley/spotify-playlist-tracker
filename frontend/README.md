# Frontend - GitHub Pages

This directory contains the static frontend for the Spotify Playlist Tracker that will be deployed to GitHub Pages.

## Structure

- `index.html` - Landing page with features and login button

## Configuration

The API base URL is computed at runtime by `index.html`:

```javascript
// Configuration - Backend API URL (same origin when served locally; Cloudflare tunnel on GitHub Pages)
const API_BASE_URL = window.location.hostname.endsWith('github.io')
    ? 'https://spotify.4298756.xyz'
    : window.location.origin;
```

- When served via Docker Compose (frontend and backend on the same origin), `API_BASE_URL` resolves to `window.location.origin` — no configuration needed.
- When hosted on GitHub Pages, the `window.location.hostname.endsWith('github.io')` conditional selects the Cloudflare tunnel URL.

The inline `API_BASE_URL` conditional in `frontend/index.html` is the single source of truth for the backend API URL. To change the production (GitHub Pages) URL, edit that conditional in `frontend/index.html`.

## Deployment

The frontend is deployed automatically via GitHub Actions when you push to the `main` branch.

See `.github/workflows/deploy-frontend.yml` for the deployment configuration.

## Local Testing

You can test the frontend locally using any HTTP server:

```bash
# Using Python
cd frontend
python -m http.server 8000

# Using Node.js
npx http-server -p 8000

# Using PHP
php -S localhost:8000
```

Then open http://localhost:8000 in your browser.

## Important Notes

1. The frontend is a **landing page only**
2. The actual application runs on the backend (Flask templates)
3. Users click "Login with Spotify" and are redirected to the backend
4. After authentication, they use the backend-hosted web interface

This design keeps the Spotify OAuth flow secure (server-side) while providing a nice landing page on GitHub Pages.
