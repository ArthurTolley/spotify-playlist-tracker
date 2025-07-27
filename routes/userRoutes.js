const express = require('express');
const User = require('../models/User');
const router = express.Router();

// Route for user registration
router.post('/register', async (req, res) => {
    const { username, password } = req.body;
    const newUser = new User({ username, password });
    try {
        await newUser.save();
        res.status(201).send('User registered successfully');
    } catch (error) {
        res.status(400).send('Error registering user: ' + error.message);
    }
});

// Other user-related routes can go here

module.exports = router;
