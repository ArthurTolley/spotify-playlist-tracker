import datetime
from spotify_playlist_tracker.utils import add_track_information

def test_add_track_information():
    # Define test data
    tracks = ['track_id_1', 'track_id_2', 'track_id_3']

    # Call the function
    result = add_track_information(tracks)

    # Assert that the function returned the expected track information
    assert result == {
        'track_id_1': {
            'removed': False,
            'date_added': datetime.date.today().strftime('%d %b %Y')
        },
        'track_id_2': {
            'removed': False,
            'date_added': datetime.date.today().strftime('%d %b %Y')
        },
        'track_id_3': {
            'removed': False,
            'date_added': datetime.date.today().strftime('%d %b %Y')
        }
    }