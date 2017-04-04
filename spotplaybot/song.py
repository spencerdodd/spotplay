

class Song:
	def __init__(self, name, artist, album=""):
		self.name = name
		self.artist = artist
		self.album = album
		self.song_id = None

	def get_search_string(self):
		return "{} {}".format(self.name, self.artist)

	def get_album_search_string(self):
		return "{} {}".format(self.artist, self.album)

	def __hash__(self):
		return hash(self.name + self.artist + self.album)

	def __eq__(self, other):
		return self.name == other.name and self.artist == other.artist and self.album == other.album
