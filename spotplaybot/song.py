import codecs

class Song:
	def __init__(self, name, artist, album=""):
		self.name = name.encode('utf-8')
		self.artist = artist.encode('utf-8')
		self.album = album.encode('utf-8')

	def get_search_string(self):
		return "{} {}".format(self.name, self.artist)