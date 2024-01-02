import unittest
from unittest.mock import patch, MagicMock
from context import spotify_playlist_tracker

class TestCreatePlaylist(unittest.TestCase):

    @patch('your_module.requests.post')
    def test_create_playlist_success(self, mock_post):
        # Mock the requests.post method
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'id': 'mock_playlist_id'}
        mock_post.return_value = mock_response

        # Call the function with mock data
        token = 'mock_token'
        user_id = 'mock_user_id'
        playlist_name = 'Test Playlist'

        result = utils.create_playlist(token, user_id, playlist_name)

        # Assert that the function returned the expected playlist_id
        self.assertEqual(result, 'mock_playlist_id')

        # Assert that requests.post was called with the expected parameters
        mock_post.assert_called_once_with(
            f'https://api.spotify.com/v1/users/{user_id}/playlists',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            data='{"name": "Test Playlist", "public": true}'
        )

    @patch('your_module.requests.post')
    def test_create_playlist_failure(self, mock_post):
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
        self.assertIsNone(result)

        # Assert that requests.post was called with the expected parameters
        mock_post.assert_called_once_with(
            f'https://api.spotify.com/v1/users/{user_id}/playlists',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
            data='{"name": "Test Playlist", "public": true}'
        )

if __name__ == '__main__':
    unittest.main()
