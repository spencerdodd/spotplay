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


class SpotPlayBot:
	def __init__(self):
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
			client_credentials_manager = SpotifyClientCredentials(config.spotify_client_id, config.spotify_client_secret)
			self.spotify_api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
		except SpotifyOauthError:
			raise Exception("Authorization failed! (spotify)")

	def get_spotify_posts(self):
		subreddit = self.reddit.subreddit(config.subreddit)
		posts_to_scrape = []

		for submission in subreddit.hot(limit=10):
			if "spotify" and "playlist" in submission.url:
				submission.comments.replace_more()
				comments = submission.comments.list()
				previously_processed = False
				for comment in comments:
					if config.signature in comment.body:
						previously_processed = True

				if not previously_processed:
					posts_to_scrape.append(submission)

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
				self.google_api.add_songs_to_playlist(new_playlist_id,song_id)
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
					" playlist\n\n[Playlist]({})\n\nI am a bot, this was performed automatically.\n" \
					"If there is a problem with this post, please contact /u/aztechk\n\n*{}*\n\n" \
					"---------------------\n\n" \
					"^Source ^code: ^[Github]({})".format(share_link, config.signature, config.github_url)
		post.reply(post_text)

	def run(self):
		while True:
			for post in self.get_spotify_posts():
				post_playlist = self.spotify_list_playlist(post.url)
				share_link = self.google_create_playlist(post_playlist)
				self.post_message_in_thread(post, share_link)

				print ("Complete!")

			time.sleep(120)


def main():
	bot = SpotPlayBot()
	bot.run()

if __name__ == "__main__":
	main()
