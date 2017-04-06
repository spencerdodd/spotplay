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

    def from_text_link(self, text_link):
        split_link = text_link.split("-")
        self.title = split_link[1].strip()
        self.artists = split_link[0].strip()
        self.album = ""

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

