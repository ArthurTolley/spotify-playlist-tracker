import os
from unittest.mock import patch
from spotify_playlist_tracker.utils import get_access_token

@patch('spotify_playlist_tracker.utils.SpotifyOAuth.get_access_token')
def test_get_access_token(mock_get_access_token):
    # Mock the SpotifyOAuth.get_access_token method
    mock_token_info = {'access_token': 'mock_token'}
    mock_get_access_token.return_value = mock_token_info

    # Set the required environment variables
    os.environ['SPOTIPY_CLIENT_ID'] = 'mock_client_id'
    os.environ['SPOTIPY_CLIENT_SECRET'] = 'mock_client_secret'

    # Call the function
    result = get_access_token()

    # Assert that the function returned the expected access token
    assert result == 'mock_token'

    # Assert that SpotifyOAuth.get_access_token was called
    mock_get_access_token.assert_called_once()

    # Reset the environment variables
    del os.environ['SPOTIPY_CLIENT_ID']
    del os.environ['SPOTIPY_CLIENT_SECRET']
