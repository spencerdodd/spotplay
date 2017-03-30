# External Libs
import time
import traceback

import praw
import spotipy
from gmusicapi import Mobileclient
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError
from twilio.rest import TwilioRestClient

from song import Song
# Internal Libs
from spotplaybot import config

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

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		# youtube
		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		self.youtube_api = build(config.youtube_api_service_name, config.youtube_api_version, developerKey=config.youtube_api_key)
		try:
			# TODO
			pass
		except Exception as e:
			raise Exception("Authorization failed! (youtube)")

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		# twilio
		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		self.twilio_client = TwilioRestClient(config.twilio_account_sid, config.twilio_auth_token)

		print ("Successfully authorized")

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		# load subreddits
		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
		self.subreddits = []

		for subreddit in config.subreddits:
			self.subreddits.append(self.reddit.subreddit(subreddit))
			print ("Connected to subreddit {}".format(subreddit))

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def get_spotify_posts(self, subreddit):
		print ("Searching for spotify playlists to re-host")
		posts_to_scrape = []

		for idx, submission in enumerate(subreddit.hot(limit=25)):
			if "spotify" and "playlist" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
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
			scraped_song = Song(song_name, song_artist, album=song_album)
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

	def parse_songs_from_comment(self, comment_text):
		lines = comment_text.split("\n\n")
		parsed_songs = []

		for idx, dirty_line in enumerate(lines):
			line = dirty_line.encode('utf-8')
			if "spotify.com" in line:
				pass
				# parsed_song = self.spotify_convert_link_to_song(line)
				# parsed_songs.append(parsed_song)

			elif "play.google.com" in line:
				pass
				# parsed_song = self.google_convert_link_to_song(line)
				# parsed_songs.append(parsed_song)

			elif "youtube.com" in line and not "playlist" in line:
				parsed_youtube_link = self.parse_youtube_link_from_line(line)
				parsed_song = self.youtube_convert_link_to_song(parsed_youtube_link)
				if parsed_song.name != "":
					parsed_songs.append(parsed_song)

			else:
				if len(line.split("-")) == 2 and line[line.index("-")-1] == " " and line[line.index("-")+1] == " ":
					print "Processing line {} | {} |".format(idx, line)
					song_info = line.split("-")
					parsed_song = Song(song_info[0], song_info[1])
					parsed_songs.append(parsed_song)

		return parsed_songs

	# TODO jesus christ write a regex
	def parse_youtube_link_from_line(self, comment_link):
		split_link = comment_link.split("](")

		if len(split_link) == 1:
			if ")" in split_link:
				right_bound = split_link.index(")")
				return split_link[0][:right_bound]
			else:
				return split_link[0]
		else:
			if ")" in split_link:
				right_bound = split_link.index(")")
				return split_link[1][:right_bound]
			else:
				return split_link[1][:-1]

	def parse_songs_from_submission(self, submission):
		submission.comments.replace_more()
		songs = []

		for comment in submission.comments.list():
			songs += self.parse_songs_from_comment(comment.body)

		return songs

	# TODO
	def spotify_convert_link_to_song(self, link):
		pass

	# TODO
	def google_convert_link_to_song(self, link):
		pass

	def youtube_convert_link_to_song(self, link):
		print ("link: {}".format(link))
		video_id = link.split("?v=")[1]
		video_info = self.youtube_api.videos().list(
			part="snippet,localizations",
			id=video_id
  		).execute()
		print video_info
		try:
			video_title = video_info["items"][0]["snippet"]["title"]
			split_info = video_title.split("-")
			if len(split_info) == 1:
				parsed_song = Song(split_info[0], "")					# just make it the song
			else:
				parsed_song = Song(split_info[0], split_info[1])

			return parsed_song
		except:
			# no results on the search
			return Song("","","")

	def post_message_in_thread(self, post, share_link, type="submission"):
		if type == "submission":
			print ("Posting message to thread")
			post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the posted Spotify" \
						" playlist\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
			post.reply(post_text)
		elif type == "comment":
			print ("Posting message to thread")
			post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the parent" \
						" comment\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
			post.reply(post_text)
		elif type == "thread":
			print ("Posting message to thread")
			post_text = "Here is an automatically-generated Google Play Music playlist of the songs in this thread" \
						"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
			post.reply(post_text)

	def remove_repeats(self, song_list):
		return list(set(song_list))

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# context methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def get_uptime(self, comment):
		print ("Getting uptime and replying to comment")
		uptime_seconds = time.time() - self.start_time
		uptime_hours = uptime_seconds / 60
		uptime_days = uptime_hours / 24

		message = "**Uptime Statistics for spotplaybot**\n\nspotplaybot has been up for:\n\n" \
				  "{} hours\n\n{}".format(uptime_hours, config.signature)

		comment.reply(message)

		print ("Comment posted!")

	def get_parent_comment_links(self, comment):
		print ("Converting links in parent comment")
		comment_parent = comment.parent()
		if hasattr(comment_parent, "replies"):
			songs = self.parse_songs_from_comment(comment_parent.body)
			songs = self.remove_repeats(songs)
			share_link = self.google_create_playlist(songs)
			self.post_message_in_thread(comment, share_link, type="comment")

			print ("Complete!")
		else:
			print ("Cannot convert a non-comment parent")

	def get_all_thread_links(self, comment):
		print ("Converting links from full submission")
		songs = self.parse_songs_from_submission(comment.submission)
		songs = self.remove_repeats(songs)
		share_link = self.google_create_playlist(songs)
		self.post_message_in_thread(comment, share_link, type="thread")

		print ("Complete")

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# base methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def process_spotify_threads(self, subreddit):
		for post in self.get_spotify_posts(subreddit):
			post_playlist = self.spotify_list_playlist(post.url)
			share_link = self.google_create_playlist(post_playlist)
			self.post_message_in_thread(post, share_link)

	def process_context_calls(self, subreddit):
		"""
		Scrapes comments of threads in given subreddit for mentions that fit the defined functionality. If there is
		a mention, then process that functionality.
			- uptime
			- convert thread
			- link song
		
		"""
		print ("Searching for context calls")
		context_calls = {
			"{} uptime".format(config.context_clue): self.get_uptime,
			"{} convert links".format(config.context_clue): self.get_parent_comment_links,
			"{} convert thread".format(config.context_clue): self.get_all_thread_links,
			# "{} convert song".format(config.context_clue): self.convert_song
		}
		for submission in subreddit.hot(limit=25):
			submission.comments.replace_more()
			for comment in submission.comments.list():
				for context_call in context_calls.keys():
					if context_call in comment.body and not self.previously_processed_comment(comment):
						context_calls[context_call](comment)

		print ("No more context calls found")

	def previously_processed_submission(self, submission):
		previously_processed = False
		for comment in submission.comments:
			if config.signature in comment.body:
				previously_processed = True

		return previously_processed

	def previously_processed_comment(self, comment):
		previously_processed = False
		for second_level_comment in comment.replies:
			if config.signature in second_level_comment.body:
				previously_processed = True

		return previously_processed

	def run(self):
		while True:
			try:
				for subreddit in self.subreddits:
					self.process_spotify_threads(subreddit)
					self.process_context_calls(subreddit)
					print ("Processing /r/{} Complete!".format(subreddit))

				time.sleep(10)
				raise Exception("test kill")

			except Exception as e:
				message_body = "Bot is kill.\n{}".format(traceback.format_exc(e))
				message = self.twilio_client.messages.create(to=config.twilio_to_number,
															 from_=config.twilio_from_number,
															 body="{}".format(message_body))
				print message_body
				raise


def main():
	bot = SpotPlayBot()
	bot.run()


if __name__ == "__main__":
	main()
