// Function to extract Spotify user ID from URL
const isSpotifyUserId = (input) => {
    // Check if the input is a valid URL
    const urlPattern = /^(https?:\/\/)?(www\.)?(open\.spotify\.com\/user\/\d+)/;

    // Check if the input matches the URL pattern
    if (urlPattern.test(input)) {
        // If it's a URL, extract the user ID
        const matches = input.match(/\/user\/(\d+)/);
        return matches ? matches[1] : null; // Return the user ID if found
    }

    // If it's not a URL, assume it's just the user ID (if it's a number)
    return /^\d+$/.test(input) ? input : null; // Return the user ID or null
};

module.exports = {
    isSpotifyUserId,
};
