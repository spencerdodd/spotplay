# External Libs
import praw
import time
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError
from gmusicapi import Mobileclient

# Internal Libs
import config
from song import Song

oauth_url = "https://oauth.reddit.com"
reddit_url = "https://www.reddit.com"
short_reddit_url = "https://redd.it"


# TODO
# 1. title of playlist should be the title of the submission that linked the playlist
# 2. youtube 		-------> 		google play music
# 3. all sources 	-------> 		spotify


class SpotPlayBot:
	def __init__(self):
		self.start_time = time.time()

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		# reddit
		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		self.reddit = praw.Reddit(client_id=config.reddit_id,
								  client_secret=config.reddit_secret,
								  user_agent=config.user_agent,
								  username=config.reddit_username,
								  password=config.reddit_password)

		if self.reddit.read_only:
			raise Exception("Authorization failed! (reddit)")

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		# google
		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		self.google_api = Mobileclient()
		self.google_api.login(config.google_email, config.google_password, '1234567890abcdef')
		if not self.google_api.is_authenticated():
			raise Exception("Authorization failed! (google)")

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		# spotify
		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		try:
			client_credentials_manager = SpotifyClientCredentials(config.spotify_client_id,
																  config.spotify_client_secret)
			self.spotify_api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
		except SpotifyOauthError:
			raise Exception("Authorization failed! (spotify)")

		print ("Successfully authorized")

		self.subreddit = self.reddit.subreddit(config.subreddit)

		print ("Connected to subreddit {}".format(config.subreddit))

	def get_spotify_posts(self):
		print ("Searching for spotify playlists to re-host")
		posts_to_scrape = []

		for idx, submission in enumerate(self.subreddit.hot(limit=25)):
			if "spotify" and "playlist" in submission.url:
				submission.comments.replace_more()
				comments = submission.comments.list()
				previously_processed = False
				for comment in comments:
					if self.previously_processed(comment):
						previously_processed = True

				if not previously_processed:
					posts_to_scrape.append(submission)

		if len(posts_to_scrape) == 0:
			print ("No new posts to re-host")

		return posts_to_scrape

	def spotify_list_playlist(self, url_to_scrape):
		print ("Scraping playlist at: {}".format(url_to_scrape))
		user_id = url_to_scrape.split("user/")[1].split("/")[0]
		playlist_id = url_to_scrape.split("/")[-1]
		playlist = self.spotify_api.user_playlist_tracks(user_id, playlist_id)
		songs_by_name = []

		for item in playlist["items"]:
			song = item["track"]
			song_name = song["name"]
			song_artist = song["artists"][0]["name"]
			song_album = song["album"]["name"]
			scraped_song = Song(song_name, song_artist, song_album)
			songs_by_name.append(scraped_song)

		return songs_by_name

	def google_create_playlist(self, list_of_song_objects):
		print ("Creating gplaymusic playlist")
		playlist_number = 0

		for playlist in self.google_api.get_all_playlists():
			if "spotplaybot" in playlist["name"]:
				playlist_number += 1

		playlist_title = "spotplaybot{}".format(playlist_number)
		new_playlist_id = self.google_api.create_playlist(playlist_title)

		for song in list_of_song_objects:
			song_id = self.get_song_from_search(song)
			if song_id != config.search_failure_string:
				print ("Adding {}".format(song.get_search_string()))
				self.google_api.add_songs_to_playlist(new_playlist_id, song_id)
			else:
				print ("Could not find {} in Google Play Music".format(song.get_search_string()))

		print ("Making playlist {} public".format(playlist_title))
		self.google_api.edit_playlist(new_playlist_id, public=True)

		share_link = "https://play.google.com/music/playlist/"
		for playlist in self.google_api.get_all_playlists():
			if playlist["id"] == new_playlist_id:
				share_link += playlist["shareToken"]

		print ("Share link: {}".format(share_link))

		return share_link

	def get_song_from_search(self, song_to_search):
		hits = self.google_api.search(song_to_search.get_search_string())["song_hits"]

		if len(hits) > 0:
			return hits[0]["track"]["storeId"]

		else:
			return config.search_failure_string

	def post_message_in_thread(self, post, share_link):
		print ("Posting message to thread")
		post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the posted Spotify" \
					" playlist\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
		post.reply(post_text)

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# context methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def get_uptime(self, comment):
		print ("Getting uptime and replying to comment")
		uptime_seconds = time.time() - self.start_time
		uptime_hours = uptime_seconds / 60
		uptime_days = uptime_hours / 24

		message = "**Uptime Statistics for spotplay-bot**\n\nspotplay-bot has been up for:\n\n" \
				  "{} hours\n\n{}".format(uptime_hours, config.signature)

		comment.reply(message)

		print ("Comment posted!")

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# base methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def process_spotify_threads(self):
		for post in self.get_spotify_posts():
			post_playlist = self.spotify_list_playlist(post.url)
			share_link = self.google_create_playlist(post_playlist)
			self.post_message_in_thread(post, share_link)

			print ("Complete!")

	def process_context_calls(self):
		"""
		Scrapes comments of threads in given subreddit for mentions that fit the defined functionality. If there is
		a mention, then process that functionality.
			- uptime
			- convert thread
			- convert song
		
		"""
		print ("Searching for context calls")
		context_calls = {
			"{} uptime".format(config.context_clue): self.get_uptime,
			# "{} convert thread".format(config.context_clue):self.convert_thread,
			# "{} convert song".format(config.context_clue): self.convert_song
		}
		for submission in self.subreddit.hot(limit=25):
			submission.comments.replace_more()
			for comment in submission.comments.list():
				for context_call in context_calls.keys():
					if context_call in comment.body and not self.previously_processed(comment):
						context_calls[context_call](comment)

		print ("No more context calls found")

	def previously_processed(self, comment):
		previously_processed = False
		for second_level_comment in comment.replies:
			if config.signature in second_level_comment.body:
				previously_processed = True

		return previously_processed

	def restart(self):
		self.__init__()

	def run(self):
		while True:
			try:
				self.process_spotify_threads()
				self.process_context_calls()

				time.sleep(10)

			except Exception as e:
				print ("Base error encountered, restarting bot\n{}".format(str(e)))
				self.restart()


def main():
	bot = SpotPlayBot()
	bot.run()


if __name__ == "__main__":
	main()
