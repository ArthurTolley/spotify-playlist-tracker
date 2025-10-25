# Frontend - GitHub Pages

This directory contains the static frontend for the Spotify Playlist Tracker that will be deployed to GitHub Pages.

## Structure

- `index.html` - Landing page with features and login button
- `config.js` - Configuration file for API endpoints

## Configuration

Before deploying, update the following:

### 1. Update `index.html`

Find this line and replace with your actual Cloudflare tunnel URL:
```javascript
const API_BASE_URL = 'https://your-domain.com'; // Change this to your actual domain
```

### 2. Update `config.js`

```javascript
const CONFIG = {
    API_BASE_URL: 'https://spotify-tracker.yourdomain.com',
    FRONTEND_URL: 'https://yourusername.github.io/spotify-playlist-tracker',
    // ...
};
```

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
