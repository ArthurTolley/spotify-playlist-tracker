import os
import json
import datetime
from spotify_playlist_tracker.utils import save_tracks_to_json, \
                                           read_tracks_from_json, \
                                           update_tracks_json, \
                                           add_track_information

def test_save_tracks_to_json():
    # Define test data
    playlist_name = "Test Playlist"
    playlist_tracks = ["track1", "track2", "track3"]

    # Call the function
    save_tracks_to_json(playlist_name, playlist_tracks)

    # Verify that the JSON file was created
    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')
    assert os.path.exists(file_path)

    # Verify the contents of the JSON file
    with open(file_path, 'r') as file:
        saved_tracks = json.load(file)
        assert saved_tracks == playlist_tracks

    # Clean up the test environment
    os.remove(file_path)

def test_read_tracks_from_json():
    # Define test data
    playlist_name = "Test Playlist"
    existing_tracks = {
        "track1": {
            "removed": False,
            "date_added": datetime.date.today().strftime('%d %b %Y')
        },
        "track2": {
            "removed": True,
            "date_added": ""
        },
        "track3": {
            "removed": False,
            "date_added": datetime.date.today().strftime('%d %b %Y')
        }
    }

    # Create a temporary JSON file with test data
    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')
    with open(file_path, 'w') as file:
        json.dump(existing_tracks, file)

    # Call the function
    tracks = read_tracks_from_json(playlist_name)

    # Verify the returned tracks
    assert tracks == existing_tracks

    # Clean up the test environment
    os.remove(file_path)

def test_update_tracks_json():
    # Define test data
    playlist_name = "Test Playlist"
    playlist_tracks = ["track1", "track2", "track3"]
    playlist_tracks = add_track_information(playlist_tracks)

    new_tracks = ["track4", "track5"]
    removed_tracks = ["track2"]

    # Call the function
    save_tracks_to_json(playlist_name, playlist_tracks)

    # Call the function
    update_tracks_json(playlist_name, new_tracks, removed_tracks, create_backup=False)

    # Verify that the JSON file was updated
    filename = playlist_name.replace(' ', '-')
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, f'../playlists/{filename}.json')
    assert os.path.exists(file_path)

    # Verify the contents of the JSON file
    with open(file_path, 'r') as file:
        updated_tracks = json.load(file)
        assert updated_tracks["track1"]["removed"] == False
        assert updated_tracks["track2"]["removed"] == True
        assert updated_tracks["track3"]["removed"] == False
        assert updated_tracks["track4"]["removed"] == False
        assert updated_tracks["track5"]["removed"] == False
        assert updated_tracks["track1"]["date_added"] == datetime.date.today().strftime('%d %b %Y')
        assert updated_tracks["track2"]["date_added"] == datetime.date.today().strftime('%d %b %Y')
        assert updated_tracks["track3"]["date_added"] == datetime.date.today().strftime('%d %b %Y')
        assert updated_tracks["track4"]["date_added"] == datetime.date.today().strftime('%d %b %Y')
        assert updated_tracks["track5"]["date_added"] == datetime.date.today().strftime('%d %b %Y')

    # Clean up the test environment
    os.remove(file_path)