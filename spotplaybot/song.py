import codecs

class Song:
	def __init__(self, name, artist, album=""):
		self.name = name.encode('utf-8').strip()
		self.artist = artist.encode('utf-8').strip()
		self.album = album.encode('utf-8').strip()
		self.song_id = None

	def get_search_string(self):
		return "{} {}".format(self.name, self.artist)

	def __hash__(self):
		return hash(self.name + self.artist + self.album)

	def __eq__(self, other):
		return self.name == other.name and self.artist == other.artist and self.album == other.album
