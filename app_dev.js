// // Require the necessary modules
const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const path = require('path');  // Make sure 'path' is required
const { spotifyApi, getAccessToken } = require('./config/spotify');

// // Initialise the express app
const app = express();
const port = 3000;

// // Set view engine to EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));


// // Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));

// Session handling middleware
app.use(session({
    secret: 'your_secret_key', // Change this to a secure key
    resave: false,
    saveUninitialized: true,
}));

// Fetch an access token when the app starts
getAccessToken();







// // Routes for GET and POST requests
// Home page
app.get('/', (req, res) => {
    res.render('home', { playlists: null, error: null });
});


// Handle form submission for Spotify username
app.post('/playlists', async (req, res) => {
    const username = req.body.username;

    try {
        // Get the access token before making requests
        await getAccessToken();

        // Fetch user's public playlists
        const data = await spotifyApi.getUserPlaylists(username);
        res.render('home', { playlists: data.body.items, error: null });
    } catch (error) {
        console.error('Error fetching playlists:', error);
        res.render('home', { playlists: null, error: 'Error retrieving playlists. Please try again.' });
    }
});



// Start the server
app.listen(port, () => {
    console.log(`App running at http://localhost:${port}`);
});
