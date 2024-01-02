from unittest.mock import patch, MagicMock
from spotify_playlist_tracker.utils import create_playlist

@patch('spotify_playlist_tracker.utils.requests.post')
def test_create_playlist_success(mock_post):
    # Mock the requests.post method
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {'id': 'mock_playlist_id'}
    mock_post.return_value = mock_response

    # Call the function with mock data
    token = 'mock_token'
    user_id = 'mock_user_id'
    playlist_name = 'Test Playlist'

    result = create_playlist(token, user_id, playlist_name)

    # Assert that the function returned the expected playlist_id
    assert result == 'mock_playlist_id'

    # Assert that requests.post was called with the expected parameters
    mock_post.assert_called_once_with(
        f'https://api.spotify.com/v1/users/{user_id}/playlists',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        data='{"name": "Test Playlist", "public": true}'
    )

@patch('spotify_playlist_tracker.utils.requests.post')
def test_create_playlist_failure(mock_post):
    # Mock the requests.post method to simulate a failure response
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {'error': 'Bad Request'}
    mock_post.return_value = mock_response

    # Call the function with mock data
    token = 'mock_token'
    user_id = 'mock_user_id'
    playlist_name = 'Test Playlist'

    result = create_playlist(token, user_id, playlist_name)

    # Assert that the function returned None in case of failure
    assert result is None

    # Assert that requests.post was called with the expected parameters
    mock_post.assert_called_once_with(
        f'https://api.spotify.com/v1/users/{user_id}/playlists',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        data='{"name": "Test Playlist", "public": true}'
    )
