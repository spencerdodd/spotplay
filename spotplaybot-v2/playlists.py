"""
The Playlist class is the super-class of it's respective Google Play Music, Spotify, and Youtube sub-classes. It
is the end result of link-aggregation and scraping. It can also be a starting point if instantiated from a URL during
scraping. 

The multithreading code is breaking our objects and the SSL connections to the APIs...
Let's try this:
	http://stackoverflow.com/a/20722204
"""
# External Libs
import config
import traceback
import multiprocessing

# Internal Libs
from songs import Song

# Test Libs
from gmusicapi import Mobileclient


class Playlist:
	def __init__(self, name):
		self.name = name
		self.type = None
		self.url = None
		self.playlist_id = None
		self.songs = []


class GooglePlayMusicPlaylist(Playlist):

	def __init__(self, gplay_api, name):
		Playlist.__init__(self, name)
		self.gplay_api = gplay_api
		self.songs_to_add = []
		self.successful = True

		# initialize the playlist object
		self.create_playlist()
		# whether playlist creation was successful

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# Processes that use the multi-threaded timing handler
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	def __timed_process(self, method_to_process):
		p = multiprocessing.Process(target=method_to_process)
		p.start()

		# wait until process finishes or the wait limit has been reached
		p.join(config.request_wait_time)

		# if the thread is still active
		if p.is_alive():
			print ("Process took too long... Killing {}".format(method_to_process))

			# Terminate
			p.terminate()
			p.join()

	def __create_playlist(self):
		try:
			print ("[*] Trying to create playlist {}".format(self.name))
			playlist_id = self.gplay_api.create_playlist(self.name)
			self.set_playlist_id(playlist_id)
			print (vars(self))
			print ("[+] Created playlist {} [{}]".format(self.name, self.playlist_id))

		except Exception as e:
			self.successful = False
			print ("[!] Cannot connect to GooglePlayMusic API")
			print ("[!] Could not create playlist ({})".format(self.name))
			print ("{}".format(traceback.format_exc(e)))

	def __add_songs_to_playlist(self):
		try:
			print ("[*] Trying to add {} songs to playlist [{}]".format(len(self.songs_to_add), self.playlist_id))
			song_ids = [song.song_id for song in self.songs_to_add]
			songs_added = self.gplay_api.add_songs_to_playlist(self.playlist_id, song_ids)
			self.songs += self.songs_to_add
			self.songs_to_add = []
			print ("Successfully added {} songs to playlist ({}) [{}]".format(len(songs_added),
																		  self.name, self.playlist_id))
		except ValueError as ve:
			self.successful = False
			print ("[!] Did not pass a valid playlist ID ({})".format(self.playlist_id))
			print ("[!] Could not add songs to playlist ({}) [{}]".format(self.name, self.playlist_id))

		except Exception as e:
			self.successful = False
			print ("[!] Cannot connect to GooglePlayMusic API")
			print ("[!] Could not add songs to playlist ({}) [{}]".format(self.name, self.playlist_id))

	def __publish_playlist(self):
		try:
			print ("[*] Publishing Playlist ({}) [{}]".format(self.name, self.playlist_id))
			self.gplay_api.edit_playlist(self.playlist_id, public=True)
			print ("[+] Successfully published playlist ({}) [{}]".format(self.name, self.playlist_id))

		except ValueError as ve:
			self.successful = False
			print ("[!] Did not pass a valid playlist ID ({})".format(self.playlist_id))
			print ("[!] Could not publish playlist ({}) [{}]".format(self.name, self.playlist_id))

		except Exception as e:
			self.successful = False
			print ("[!] Cannot connect to GooglePlayMusic API")
			print ("[!] Could not publish playlist ({}) [{}]".format(self.name, self.playlist_id))

	def __delete_playlist(self):
		try:
			print ("[*] Deleting Playlist ({}) [{}]".format(self.name, self.playlist_id))
			self.gplay_api.delete_playlist(self.playlist_id)
			print ("[+] Successfully deleted playlist ({}) [{}]".format(self.name, self.playlist_id))

		except ValueError as ve:
			self.successful = False
			print ("[!] Did not pass a valid playlist ID ({})".format(self.playlist_id))
			print ("[!] Could not delete playlist ({}) [{}]".format(self.name, self.playlist_id))

		except Exception as e:
			self.successful = False
			print ("[!] Cannot connect to GooglePlayMusic API")
			print ("[!] Could not delete playlist ({}) [{}]".format(self.name, self.playlist_id))

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# Handlers
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def add_songs_to_playlist(self, songs_to_add):
		self.songs_to_add += songs_to_add
		self.__add_songs_to_playlist
		#self.__timed_process(self.__add_songs_to_playlist)

	def create_playlist(self):
		print (vars(self))
		self.playlist_id = self.gplay_api.create_playlist(self.name)
		#self.__timed_process(self.__create_playlist)
		print (vars(self))

	def delete_playlist(self):
		self.gplay_api.delete_playlist(self.playlist_id)

		#self.__timed_process(self.__delete_playlist)

	def publish_playlist(self):
		self.__timed_process(self.__publish_playlist)

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# Getters and Setters
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	def set_playlist_id(self, playlist_id):
		self.playlist_id = playlist_id


class SpotifyPlaylist(Playlist):
	def __init__(self, name):
		Playlist.__init__(self, name)


class YoutubePlaylist(Playlist):
	def __init__(self, name):
		Playlist.__init__(self, name)


def google_playlist_tests():

	test_song1 = Song()
	test_song1.from_text_link("Porter Robinson - Divinity")
	test_song1.song_id = "Tkyyz7bclv2fyr2esgy5o23podu"
	test_song2 = Song()
	test_song2.from_text_link("Nicolas Jaar - Fight")
	test_song2.song_id = "T2blniervtcelsosbqda5wd4hxe"

	test_api = Mobileclient()
	test_api.login(config.google_email, config.google_password, '1234567890abcdef')
	if not test_api.is_authenticated():
		raise Exception("[!] Authorization failed! (google)")

	test_playlist = GooglePlayMusicPlaylist(test_api, "Test Playlist")
	test_playlist.add_songs_to_playlist([test_song1, test_song2])
	test_playlist.delete_playlist()

if __name__ == "__main__":
	google_playlist_tests()