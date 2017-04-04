"""
The Submission class is used to process submissions (Reddit threads) that fit a handle-able criteria. Some of the
intended functionality includes:
    * conversion of Spotify links into Google Play Music playlists
"""


class Submission:
    def __init__(self, submission):
        self.submission = submission
        self.thread_url = None
        self.linked_url = None
        self.playlist = None

"""
The Comment class is used to create objects that handle contextual calls to the bot. Some functionality includes:
    * in-line link conversion
        i.e. `musicbot convert link https://www.youtube.com/watch?v={video-id}`
    * thread link conversion
        i.e. `musicbot convert thread tracks` or `musicbot convert thread albums`
    * shit-posting
        i.e. `musicbot all time greatest tracks` -> playlist of 100 copies of Darude - Sandstorm
"""


class Comment:
    def __init__(self, comment):
        self.comment = comment
        self.thread_url = None
        self.linked_url = None
        self.playlist = None
