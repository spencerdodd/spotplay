import praw
import time
import config
import spotipy
import datetime
import traceback
from song import Song
from gmusicapi import Mobileclient
from twilio.rest import TwilioRestClient
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Logging
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# TODO
# 1. Don't create playlist if there are no songs that were parsed
# 2. Spotify tracks -> google play music
# 3. Convert all linked audio to google play (youtube posts as well)
# 4. all sources 	-------> 		spotify


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
		self.current_subreddit = ""

		for subreddit in config.subreddits:
			self.subreddits.append(self.reddit.subreddit(subreddit))
			print ("Connected to subreddit {}".format(subreddit))

		# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def get_spotify_playlist_posts(self, subreddit):
		print ("[/r/{}] Searching for spotify playlists to re-host".format(self.current_subreddit))
		posts_to_scrape = []

		for idx, submission in enumerate(subreddit.hot(limit=config.post_threshold)):
			if "spotify" in submission.url and "playlist" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
					posts_to_scrape.append(submission)

		if len(posts_to_scrape) == 0:
			print ("[/r/{}] No new posts to re-host".format(self.current_subreddit))

		return posts_to_scrape

	def get_spotify_album_posts(self, subreddit):
		print ("[/r/{}] Searching for spotify albums to re-host".format(self.current_subreddit))
		posts_to_scrape = []

		for idx, submission in enumerate(subreddit.hot(limit=config.post_threshold)):
			if "spotify" in submission.url and "album" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
					posts_to_scrape.append(submission)

		if len(posts_to_scrape) == 0:
			print ("[/r/{}] No new posts to re-host".format(self.current_subreddit))

		return posts_to_scrape

	def get_spotify_track_posts(self, subreddit):
		print ("[/r/{}] Searching for spotify tracks to re-host".format(self.current_subreddit))
		posts_to_scrape = []

		for idx, submission in enumerate(subreddit.hot(limit=config.post_threshold)):
			if "spotify" in submission.url and "track" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
					posts_to_scrape.append(submission)

		if len(posts_to_scrape) == 0:
			print ("[/r/{}] No new posts to re-host".format(self.current_subreddit))

		return posts_to_scrape

	def spotify_list_playlist(self, url_to_scrape):
		print ("[/r/{}] Scraping playlist at: {}".format(self.current_subreddit, url_to_scrape))
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

	def spotify_list_album(self, url_to_scrape):
		print ("[/r/{}] Scraping album at: {}".format(self.current_subreddit, url_to_scrape))
		album_id = url_to_scrape.split("album/")[1]
		album = self.spotify_api.album(album_id)
		album_name = album["name"]
		raw_artists = album["artists"]
		album_artists = []
		for artist in raw_artists:
			artist_name = artist["name"]
			album_artists.append(artist_name)
		songs_by_name = []

		for track in album["tracks"]["items"]:
			track_name = track["name"]
			track_artists = album_artists[0]

			scraped_song = Song(track_name, track_artists, album=album_name)
			songs_by_name.append(scraped_song)

			print ("added song")
			print (scraped_song.get_search_string())

		return songs_by_name

	def spotify_list_track(self, url_to_scrape):
		print ("[/r/{}] Scraping song at: {}".format(self.current_subreddit, url_to_scrape))
		track_id = url_to_scrape.split("track/")[1]
		track = self.spotify_api.track(track_id)
		track_name = track["name"]
		track_artists = track["artists"][0]["name"]
		track_album = track["album"]["name"]
		scraped_songs = []
		scraped_song = Song(track_name, track_artists, album=track_album)
		scraped_songs.append(scraped_song)

		return scraped_songs

	def google_create_playlist(self, list_of_song_objects):
		if len(list_of_song_objects) > 0:
			print ("[/r/{}] Creating gplaymusic playlist".format(self.current_subreddit))

			cdt = datetime.datetime.today()
			playlist_title = "[/r/{}] {}-{}-{}".format(self.current_subreddit, cdt.year, cdt.month, cdt.day)
			new_playlist_id = self.google_api.create_playlist(playlist_title)
			songs_to_add = []

			for song in list_of_song_objects:
				print "[/r/{}] searching for {}".format(self.current_subreddit, song.get_search_string())
				song_id = self.get_song_from_search(song)
				song.song_id = song_id
				if song.song_id != config.search_failure_string:
					songs_to_add.append(song)
				else:
					print ("[/r/{}] Could not find {} in Google Play Music".format(self.current_subreddit,
																				song.get_search_string()))

			if len(songs_to_add) > 0:
				for song in songs_to_add:
					print ("[/r/{}] Adding {}".format(self.current_subreddit, song.get_search_string()))
					print (vars(song))
					self.google_api.add_songs_to_playlist(new_playlist_id, song.song_id)
				print ("[/r/{}] Making playlist {} public".format(self.current_subreddit, playlist_title))
				self.google_api.edit_playlist(new_playlist_id, public=True)

				share_link = "https://play.google.com/music/playlist/"
				for playlist in self.google_api.get_all_playlists():
					if playlist["id"] == new_playlist_id:
						share_link += playlist["shareToken"]

				print ("[/r/{}] Share link: {}".format(self.current_subreddit, share_link))

				return share_link
			else:
				print ("[/r/{}] Deleting empty gplaymusic playlist".format(self.current_subreddit))
				self.google_api.delete_playlist(new_playlist_id)
				return config.empty_playlist_link

		else:
			return config.empty_playlist_link

	def get_song_from_search(self, song_to_search):
		hits = self.google_api.search(song_to_search.get_search_string())["song_hits"]

		if len(hits) == 1:
			print ("found {} in gplay (1 hit)".format(song_to_search.get_search_string()))
			return hits[0]["track"]["storeId"]
		elif len(hits) > 1:
			for track in hits:
				if song_to_search.artist in track["track"]["albumArtist"]:
					print ("{} in {}".format(song_to_search.get_search_string, track["track"]))
					return track["track"]["storeId"]

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

			elif "youtube.com" in line and not "playlist" in line and not "channel" in line:
				parsed_youtube_links = self.parse_youtube_links_from_line(line)
				for parsed_youtube_link in parsed_youtube_links:
					parsed_song = self.youtube_convert_link_to_song(parsed_youtube_link)
					if parsed_song.name != "":
						parsed_songs.append(parsed_song)

			else:
				if len(line.split("-")) == 2 and line[line.index("-")-1] == " " and line[line.index("-")+1] == " ":
					print ("[/r/{}] Processing line {} | {} |".format(self.current_subreddit, idx, line))
					song_info = line.split("-")
					parsed_song = Song(song_info[0], song_info[1])
					parsed_songs.append(parsed_song)

		return parsed_songs

	# TODO jesus christ write a regex
	def parse_youtube_links_from_line(self, comment_link):
		links = []
		while "https://www.youtube.com/watch" in comment_link:
			link_index = comment_link.index("https://www.youtube.com/watch")
			link = comment_link[link_index:link_index+43]
			links.append(link)
			comment_link = comment_link[link_index+43:]
		return links

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
		print ("[/r/{}] link: {}".format(self.current_subreddit, link))
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
		if share_link != config.empty_playlist_link:
			if type == "submission":
				print ("[/r/{}] Posting message to thread".format(self.current_subreddit))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the posted Spotify" \
							" playlist\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "comment":
				print ("[/r/{}] Posting message to thread".format(self.current_subreddit))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the parent" \
							" comment\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "thread":
				print ("[/r/{}] Posting message to thread".format(self.current_subreddit))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in this thread" \
							"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "album":
				print ("[/r/{}] Posting message to thread".format(self.current_subreddit))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the posted Spotify" \
							" album\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "track":
				print ("[/r/{}] Posting message to thread".format(self.current_subreddit))
				post_text = "Here is an automatically-generated Google Play Music playlist of the posted Spotify track" \
							"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
		else:
			print ("[/r/{}] Not posting, playlist was empty".format(self.current_subreddit))

	def remove_repeats(self, song_list):
		return list(set(song_list))

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# context methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def get_uptime(self, comment):
		print ("[/r/{}] Getting uptime and replying to comment".format(self.current_subreddit))
		uptime_seconds = time.time() - self.start_time
		uptime_hours = uptime_seconds / 60
		uptime_days = uptime_hours / 24

		message = "**Uptime Statistics for spotplaybot**\n\nspotplaybot has been up for:\n\n" \
				  "{} hours\n\n{}".format(uptime_hours, config.signature)

		comment.reply(message)

		print ("[/r/{}] Comment posted!".format(self.current_subreddit))

	def get_parent_comment_links(self, comment):
		print ("[/r/{}] Converting links in parent comment".format(self.current_subreddit))
		comment_parent = comment.parent()
		if hasattr(comment_parent, "replies"):
			songs = self.parse_songs_from_comment(comment_parent.body)
			songs = self.remove_repeats(songs)
			share_link = self.google_create_playlist(songs)
			self.post_message_in_thread(comment, share_link, type="comment")

			print ("[/r/{}] Complete!".format(self.current_subreddit))
		else:
			print ("Cannot convert a non-comment parent")

	def get_all_thread_links(self, comment):
		print ("[/r/{}] Converting links from full submission".format(self.current_subreddit))
		songs = self.parse_songs_from_submission(comment.submission)
		songs = self.remove_repeats(songs)
		share_link = self.google_create_playlist(songs)
		self.post_message_in_thread(comment, share_link, type="thread")

		print ("[/r/{}] Complete".format(self.current_subreddit))

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# base methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def process_spotify_threads(self, subreddit):
		for post in self.get_spotify_playlist_posts(subreddit):
			post_playlist = self.spotify_list_playlist(post.url)
			share_link = self.google_create_playlist(post_playlist)
			self.post_message_in_thread(post, share_link)

		for post in self.get_spotify_album_posts(subreddit):
			post_album = self.spotify_list_album(post.url)
			share_link = self.google_create_playlist(post_album)
			self.post_message_in_thread(post, share_link, type="album")

		for post in self.get_spotify_track_posts(subreddit):
			post_track = self.spotify_list_track(post.url)
			share_link = self.google_create_playlist(post_track)
			self.post_message_in_thread(post, share_link, type="track")

	def process_context_calls(self, subreddit):
		"""
		Scrapes comments of threads in given subreddit for mentions that fit the defined functionality. If there is
		a mention, then process that functionality.
			- uptime
			- convert thread
			- link song
		
		"""
		print ("[/r/{}] Searching for context calls".format(self.current_subreddit))
		context_calls = {
			"{} uptime".format(config.context_clue): self.get_uptime,
			"{} convert links".format(config.context_clue): self.get_parent_comment_links,
			"{} convert thread".format(config.context_clue): self.get_all_thread_links,
			# "{} convert song".format(config.context_clue): self.convert_song
		}
		for submission in subreddit.hot(limit=config.post_threshold):
			submission.comments.replace_more()
			for comment in submission.comments.list():
				for context_call in context_calls.keys():
					if context_call in comment.body and not self.previously_processed_comment(comment):
						context_calls[context_call](comment)

		print ("[/r/{}] No more context calls found".format(self.current_subreddit))

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
					self.current_subreddit = config.subreddits[self.subreddits.index(subreddit)]
					self.process_spotify_threads(subreddit)
					self.process_context_calls(subreddit)
					print ("[/r/{}] Processing Complete!".format(self.current_subreddit))

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
