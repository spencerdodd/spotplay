"""
The Playlist class is the super-class of it's respective Google Play Music, Spotify, and Youtube sub-classes. It
is the end result of link-aggregation and scraping. It can also be a starting point if instantiated from a URL during
scraping. 
"""


class Playlist:
    def __init__(self, name):
        self.name = name
        self.type = None
        self.url = None
        self.id = None
        self.songs = []


class GooglePlayMusicPlaylist(Playlist):
    def __init__(self, name):
        Playlist.__init__(self, name)


class SpotifyPlaylist(Playlist):
    def __init__(self, name):
        Playlist.__init__(self, name)


class YoutubePlaylist(Playlist):
    def __init__(self, name):
        Playlist.__init__(self, name)
