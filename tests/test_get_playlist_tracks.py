import os
import requests
from unittest.mock import patch
from spotify_playlist_tracker.utils import get_playlist_tracks

@patch('spotify_playlist_tracker.utils.requests.get')
def test_get_playlist_tracks(mock_get):
    # Mock the requests.get method
    mock_response = requests.Response()
    mock_response.status_code = 200
    mock_response.json = lambda: {
            'name': 'Test Playlist',
            'owner': {'display_name': 'Test Owner'},
            'tracks': {
                'items': [
                    {'track': {'id': 'track1'}},
                    {'track': {'id': 'track2'}},
                    {'track': {'id': 'track3'}}
                ],
                'next': None
            }
    }

    mock_get.return_value = mock_response

    # Set the required token and playlist_id
    token = 'mock_token'
    playlist_id = 'mock_playlist_id'

    # Call the function
    result = get_playlist_tracks(token, playlist_id)

    # Assert that the function returned the expected track ids
    assert result == ['track1', 'track2', 'track3']

    # Assert that requests.get was called with the correct parameters
    mock_get.assert_called_once_with(
        f'https://api.spotify.com/v1/playlists/{playlist_id}',
        headers={'Authorization': f'Bearer {token}'}
    )