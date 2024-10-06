const express = require('express')
const app = express();
const port = 3000;

// Serve static files from the 'public' folder
app.use(express.static('public'));

// Route for homepage
app.get('/', (req, res) => {
    res.send('Hello World! This is my first Node.js webpage.');
});

// Start the server
app.listen(port, () => {
    console.log('App running at http://localhost:${port}');
});
