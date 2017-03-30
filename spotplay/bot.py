# External Libs
import praw
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
		pass

	def run(self):
		for post in self.get_spotify_posts():
			post_playlist = self.spotify_list_playlist(post.url)
			for song in post_playlist:
				song.format_print()


def main():
	bot = SpotPlayBot()
	bot.run()

if __name__ == "__main__":
	main()
