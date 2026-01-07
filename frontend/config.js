// Frontend Configuration
// Backend API URL via Cloudflare Tunnel

const CONFIG = {
    // Backend API URL - Cloudflare tunnel domain
    API_BASE_URL: 'https://spotify-tracker-api.4298756.xyz',
    
    // GitHub Pages URL
    FRONTEND_URL: 'https://arthurtolley.github.io/spotify-playlist-tracker',
    
    // Application info
    APP_NAME: 'Spotify Playlist Tracker',
    VERSION: '1.0.0'
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
