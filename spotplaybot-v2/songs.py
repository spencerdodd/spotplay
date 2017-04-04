"""
The Song class is used to manipulate song data
"""


class Song:
    def __init__(self):
        self.title = None
        self.artists = []
        self.album = None
        self.ids = {
            "gplay": None,
            "spotify": None,
            "youtube": None
        }

    def from_gplay_hit(self, hit):
        pass

    def from_spotify_hit(self, hit):
        pass

    def from_youtube_hit(self, hit):
        pass

"""
The Album class is used to manipulate album data
"""


class Album:
    def __init__(self):
        self.title = None
        self.artists = []
        self.ids = {
            "gplay": None,
            "spotify": None,
            "youtube": None
        }

    def from_gplay_hit(self, hit):
        pass

    def from_spotify_hit(self, hit):
        pass

    def from_youtube_hit(self, hit):
        pass

