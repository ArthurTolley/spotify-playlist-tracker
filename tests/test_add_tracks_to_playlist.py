import json
from unittest.mock import patch, MagicMock
from spotify_playlist_tracker.utils import add_tracks_to_playlist

@patch('spotify_playlist_tracker.utils.requests.post')
def test_add_tracks_to_playlist(mock_post):
    # Mock the requests.post method
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_post.return_value = mock_response

    # Set up test data
    token = 'mock_token'
    playlist_id = 'mock_playlist_id'
    track_ids = ['track_id1', 'track_id2']

    # Call the function
    add_tracks_to_playlist(token, playlist_id, track_ids)

    # Assert that requests.post was called with the correct arguments
    expected_url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    expected_headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    expected_data = {
        'uris': ['spotify:track:track_id1', 'spotify:track:track_id2'],
    }
    mock_post.assert_called_once_with(expected_url, headers=expected_headers, data=json.dumps(expected_data))

    # Assert that the appropriate message is printed
    assert mock_response.status_code == 201