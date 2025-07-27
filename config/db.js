const mongoose = require('mongoose');
require('dotenv').config();

const dbURI = `mongodb+srv://arthurellistolley:${process.env.DB_PASSWORD}@trackify.frpgr.mongodb.net/?retryWrites=true&w=majority&appName=trackify`;

const connectDB = async () => {
    try {
        await mongoose.connect(dbURI);
        console.log('Database connected successfully');
    } catch (error) {
        console.error('Database connection failed:', error);
        process.exit(1);
    }
};

module.exports = connectDB;
