import os
from unittest.mock import patch
import requests
from spotify_playlist_tracker.utils import get_user_playlists

@patch('spotify_playlist_tracker.utils.requests.get')
def test_get_user_playlists(mock_get):
    # Mock the requests.get method
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        'items': [
            {'name': 'Playlist 1', 'id': 'playlist_id_1'},
            {'name': 'Playlist 2', 'id': 'playlist_id_2'},
            {'name': 'Playlist 3', 'id': 'playlist_id_3'}
        ]
    }

    mock_get.return_value = mock_response

    # Call the function with mock data
    token = 'mock_token'
    user_id = 'mock_user_id'
    result = get_user_playlists(token, user_id)

    # Assert that the function returned the expected playlist names and ids
    assert result == {
        'playlist_names': ['Playlist 1', 'Playlist 2', 'Playlist 3'],
        'playlist_ids': ['playlist_id_1', 'playlist_id_2', 'playlist_id_3']
    }