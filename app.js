// // Require the necessary modules
const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const path = require('path');  // Make sure 'path' is required

const argon2 = require('argon2');
const User = require('./models/User'); // Import the User model
const connectDB = require('./config/db'); // Import the connectDB function
const { spotifyApi, getAccessToken } = require('./config/spotify');  // Spotify API configuration
const { isSpotifyUserId } = require('./utils/utils');



// // Initialise the express app
const app = express();
const port = 3000;
// Connect to MongoDB
connectDB();
getAccessToken();

// // Set view engine to EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// // Middleware
// Body parser middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));

// Session handling middleware
app.use(session({
    secret: 'your_secret_key', // Change this to a secure key
    resave: false,
    saveUninitialized: true,
}));

// Make the user available in all EJS templates
app.use((req, res, next) => {
    res.locals.user = req.session.user || 'Guest'; // Set 'Guest' if no user is logged in
    next();
});


// // Routes for GET and POST requests
// Home page
app.get('/', (req, res) => {
    res.render('home', { playlists: null, error: null });
});

// Login page
app.get('/login', (req, res) => {
    if (req.session.user) {
        res.render('login', { user: req.session.user });
    } else {
        res.render('login', { user: 'Guest' });
    }
});

// Handle logging in (POST)
app.post('/login', async (req, res) => {
    console.log('POST /login'); // Log the request
    const { username, password } = req.body;

    try {
        // Find the user
        const user = await User.findOne
        ({ username: username });
        if (!user) {
            return res.status(404).send('User not found');
        }

        // Compare the hashed password
        if (await argon2.verify(user.password, password)) {
            req.session.user = user; // Store the user data in the session
            res.redirect('/');
        } else {
            res.status(401).send('Incorrect password');
        }

    } catch (error) {
        console.error('Error logging in:', error);
        res.status(500).send('Error logging in');
    }
});


// Registration page
app.get('/register', (req, res) => {
    console.log('GET /register'); // Log the request
    res.render('register');
});

// Handle registration form submission (POST)
app.post('/register', async (req, res) => {
    console.log('POST /register'); // Log the request
    const { username, password } = req.body;

    try {
        // Hash the password before storing it
        const hashedPassword = await argon2.hash(password);

        // Create a new user and save to MongoDB
        const newUser = new User({
            username: username,
            password: hashedPassword, // Store the hashed password
        });

        await newUser.save();
        res.send('User registered successfully!');
    } catch (error) {
        console.error('Error registering user:', error);
        res.status(500).send('Error registering user');
    }
});

// Handle form submission for Spotify username
app.post('/playlists', async (req, res) => {

    const spotifyProfile = req.body.spotifyProfile;
    const username = isSpotifyUserId(spotifyProfile);
    console.log('POST /playlists', username); // Log the request

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



// Logging out
app.get('/logout', (req, res) => {
    req.session.destroy(); // Destroy the session
    res.redirect('/');
});



// // Final
// Start the server
app.listen(port, () => {
    console.log(`App running at http://localhost:${port}`);
});
