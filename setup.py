from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='spotify_playlist_tracker',
    version='0.1.0',
    description='Track public Spotify playlists and add new tracks to your own playlists.',
    long_description=readme,
    author='Arthur Tolley',
    author_email='arthurellistolley@gmail.com',
    url='https://github.com/ArthurTolley/spotify-playlist-tracker',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)