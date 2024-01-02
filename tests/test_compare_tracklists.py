from spotify_playlist_tracker.utils import compare_tracklists

def test_compare_tracklists():
    # Define test data
    public_tracklist = ['track_id_1', 'track_id_2', 'track_id_3', 'track_id_4']
    user_tracklist = ['track_id_2', 'track_id_3', 'track_id_5']
    user_JSON = {
        'track_id_1': {
            'removed': False,
            'date_added': '01 Jan 2022'
        },
        'track_id_2': {
            'removed': False,
            'date_added': '02 Jan 2022'
        },
        'track_id_3': {
            'removed': False,
            'date_added': '03 Jan 2022'
        }
    }

    # Call the function
    new_tracks, removed_tracks = compare_tracklists(public_tracklist, user_tracklist, user_JSON)

    # Assert that the function returned the expected new tracks and removed tracks
    assert new_tracks == ['track_id_4']
    assert removed_tracks == ['track_id_1']

    # Additional assertions can be added to test other scenarios