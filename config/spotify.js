const SpotifyWebApi = require('spotify-web-api-node');
require('dotenv').config();

// Configure the Spotify API client with client credentials
const spotifyApi = new SpotifyWebApi({
    clientId: process.env.SPOTIFY_CLIENT_ID,
    clientSecret: process.env.SPOTIFY_CLIENT_SECRET,
});

// Function to get an access token (needed for API requests)
const getAccessToken = async () => {
    try {
        const data = await spotifyApi.clientCredentialsGrant();
        spotifyApi.setAccessToken(data.body['access_token']);
    } catch (error) {
        console.error('Error retrieving access token', error);
    }
};

module.exports = {
    spotifyApi,
    getAccessToken,
};

