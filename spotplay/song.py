import codecs

class Song:
	def __init__(self, name, artist, album):
		self.name = name.encode('utf-8')
		self.artist = artist.encode('utf-8')
		self.album = album.encode('utf-8')

	def format_print(self):
		print ("\n" + "-"*15 + "\nTitle: {}\nArtist: {}\nAlbum: {}\n".format(self.name, self.artist, self.album))