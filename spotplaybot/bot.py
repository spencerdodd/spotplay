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
from kitchen.text.converters import to_unicode
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# Logging
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# TODO
# 1. youtube playlists
# 2. Convert any link type (youtube, comment, spotify) in all of the contexts
# 3. all sources 	-------> 		spotify
# 4. all sources	------->		youtube
# 5. Convert to desired playlist type in comment cue (youtube, spotify, googleplay)


class SpotPlayBot:
	def __init__(self):
		self.start_time = datetime.datetime.now()

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

		self.failures = []
		# TODO fix error that occurs when you try to upload more than 1000 songs to a playlist.
		# TODO 		..split it up into multiple playlists
		self.songs_added_to_current_playlist = 0


	def get_spotify_posts(self, subreddit):
		print ("[/r/{}] Searching for spotify posts to re-host".format(self.current_subreddit))
		posts_to_scrape = []
		for idx, submission in enumerate(subreddit.hot(limit=config.post_threshold)):
			if "spotify" in submission.url and "playlist" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
					posts_to_scrape.append(submission)

			elif "spotify" in submission.url and "album" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
					posts_to_scrape.append(submission)

			elif "spotify" in submission.url and "track" in submission.url:
				submission.comments.replace_more()

				if not self.previously_processed_submission(submission):
					posts_to_scrape.append(submission)

		if len(posts_to_scrape) == 0:
			print ("[/r/{}] No new posts to re-host".format(self.current_subreddit))

		return posts_to_scrape

	def songs_from_link(self, url_to_scrape, scrape_type="track"):
		print ("[/r/{}] Converting link {} into a song".format(self.current_subreddit, url_to_scrape))
		if "text_link" in url_to_scrape:
			try:
				if scrape_type == "album":
					print ("[/r/{}] Scraping album into tracks".format(self.current_subreddit))
					songs_by_name = {
						"type": "album",
						"songs": []
					}
					split_link = url_to_scrape.split("|")
					album_artist = split_link[1] 				# .encode('utf-8') # or .decode('utf-8').encode('utf-8)
					album_name = split_link[2]					# .encode('utf-8') # or .decode('utf-8').encode('utf-8)
					album_song_object = Song("", album_artist, album=album_name)
					album_id = self.get_id_from_search(album_song_object, search_type="album")
					print ("[/r/{}] Found album {} at {}".format(self.current_subreddit,
																 album_song_object.get_album_search_string(), album_id))
					if album_id != config.search_failure_string:
						album = self.google_api.get_album_info(album_id)
						for track in album["tracks"]:
							track_name = track["title"].encode("utf-8")
							track_artist = track["albumArtist"].encode("utf-8")
							track_id = track["storeId"].encode("utf-8")

							scraped_song = Song(track_name, track_artist)
							scraped_song.song_id = track_id

							print ("[/r/{}] Finding song : {}".format(self.current_subreddit, scraped_song.get_search_string()))

							songs_by_name["songs"].append(scraped_song)

						print ("[/r/{}] SONGS: {}".format(self.current_subreddit, songs_by_name))

						return songs_by_name

					else:
						return {"type": "album", "songs": []}

				elif scrape_type == "track":
					songs_by_name = {
						"type": "track",
						"songs": []
					}
					split_link = url_to_scrape.split("|")
					scraped_song = Song(split_link[2], split_link[1])
					songs_by_name["songs"].append(scraped_song)

					return songs_by_name

			except Exception as e:
				print ("[/r/{}] Something is wrong with the link given: {}".format(self.current_subreddit, url_to_scrape))
				return {"type": "playlist", "songs": []}

		elif "spotify" in url_to_scrape:
			try:
				if "playlist" in url_to_scrape:
					print ("[/r/{}] Scraping playlist at: {}".format(self.current_subreddit, url_to_scrape))
					user_id = url_to_scrape.split("user/")[1].split("/")[0]
					playlist_id = url_to_scrape.split("/")[-1]
					playlist = self.spotify_api.user_playlist_tracks(user_id, playlist_id)
					songs_by_name = {
						"type": "playlist",
						"songs": []
					}

					for item in playlist["items"]:
						song = item["track"]
						song_name = song["name"]
						song_artist = song["artists"][0]["name"]
						song_album = song["album"]["name"]
						scraped_song = Song(song_name, song_artist, album=song_album)
						songs_by_name["songs"].append(scraped_song)

					return songs_by_name

				elif "album" in url_to_scrape:
					print ("[/r/{}] Scraping album at: {}".format(self.current_subreddit, url_to_scrape))
					album_id = url_to_scrape.split("album/")[1]
					album = self.spotify_api.album(album_id)
					album_name = album["name"]
					raw_artists = album["artists"]
					album_artists = []
					for artist in raw_artists:
						artist_name = artist["name"]
						album_artists.append(artist_name)
					songs_by_name = {
						"type": "album",
						"songs": []
					}

					for track in album["tracks"]["items"]:
						track_name = track["name"]
						track_artists = album_artists[0]

						scraped_song = Song(track_name, track_artists, album=album_name)
						songs_by_name["songs"].append(scraped_song)

						print ("added song")
						print (scraped_song.get_search_string())

					return songs_by_name

				elif "track" in url_to_scrape:
					print ("[/r/{}] Scraping song at: {}".format(self.current_subreddit, url_to_scrape))
					track_id = url_to_scrape.split("track/")[1]
					track = self.spotify_api.track(track_id)
					track_name = track["name"]
					track_artists = track["artists"][0]["name"]
					track_album = track["album"]["name"]
					songs_by_name = {
						"type": "track",
						"songs": []
					}
					scraped_song = Song(track_name, track_artists, album=track_album)
					songs_by_name["songs"].append(scraped_song)

					return songs_by_name

			except Exception as e:
				print ("[/r/{}] Something is wrong with the link given: {}".format(self.current_subreddit, url_to_scrape))
				return {"type": "playlist", "songs": []}

		elif "youtube" in url_to_scrape:
			try:
				# https://www.youtube.com/playlist?list=PLfdkz2eiSC3a581dIX0xoQmu9te09n5ka
				if "playlist" in url_to_scrape:
					print ("[/r/{}] Scraping playlist at: {}".format(self.current_subreddit, url_to_scrape))
					playlist_id = url_to_scrape.split("list=")[1]
					playlist = self.youtube_api.playlistItems().list(
						part="snippet",
						playlistId=playlist_id,
						maxResults="50"
					).execute()
					songs_by_name = {
						"type": "playlist",
						"songs": []
					}

					for track in playlist["items"]:
						video_title = track["snippet"]["title"]
						split_title = video_title.split("-")
						if len(split_title) == 1:
							if len(split_title[0]) > 0:
								parsed_song = Song(split_title[0], "") # just make it a song
								songs_by_name["songs"].append(parsed_song)

						else:
							if len(split_title[0]) > 0 and len(split_title[1]) > 0:
								parsed_song = Song(split_title[1], split_title[0])

								songs_by_name["songs"].append(parsed_song)

					return songs_by_name

				# TODO
				elif "channel" in url_to_scrape:
					return {"type": "playlist", "songs": []}

				else:
					print ("[/r/{}] Scraping playlist at: {}".format(self.current_subreddit, url_to_scrape))
					video_id = url_to_scrape.split("?v=")[1]
					video_info = self.youtube_api.videos().list(
						part="snippet,localizations",
						id=video_id
					).execute()
					songs_by_name = {
						"type": "playlist",
						"songs": []
					}
					video_title = video_info["items"][0]["snippet"]["title"]
					split_title = video_title.split("-")
					if len(split_title) == 1:
						if len(split_title[0]) > 0:
							parsed_song = Song(split_title[0], "")  # just make it a song
							songs_by_name["songs"].append(parsed_song)
					else:
						if len(split_title[0]) > 0 and len(split_title[1]) > 0:
							parsed_song = Song(split_title[0], split_title[1])

							songs_by_name["songs"].append(parsed_song)

					return songs_by_name

			except Exception as e:
				print ("[/r/{}] Something is wrong with the link given: {}".format(self.current_subreddit, url_to_scrape))
				return {"type": "playlist", "songs": []}
		else:
			return {"type": "playlist", "songs": []}

	def google_create_playlist(self, list_of_song_objects, input_type="unsearched_songs"):
		print ("[/r/{}] Processing {} songs".format(self.current_subreddit, len(list_of_song_objects)))
		print ("[/r/{}] Songs : {}".format(self.current_subreddit, list_of_song_objects))
		if len(list_of_song_objects) > 0:
			print ("[/r/{}] Creating gplaymusic playlist".format(self.current_subreddit))
			songs_to_add = []

			if input_type == "unsearched_songs":
				for song in list_of_song_objects:
					print "[/r/{}] searching for {}".format(self.current_subreddit, song.get_search_string())
					song_id = self.get_id_from_search(song, search_type="song")
					song.song_id = song_id
					if song.song_id != config.search_failure_string and song.song_id[0] == "T":
						songs_to_add.append(song)
					else:
						print ("[/r/{}] Could not find {} in Google Play Music".format(self.current_subreddit,
																					song.get_search_string()))

			elif input_type == "searched_songs":
				print "[/r/{}] adding previously searched songs".format(self.current_subreddit)
				songs_to_add += list_of_song_objects

			if len(songs_to_add) == 0:
				print ("[/r/{}] Playlist empty".format(self.current_subreddit))
				return config.empty_playlist_link

			elif len(songs_to_add) <= 1000:
				cdt = datetime.datetime.today()
				playlist_title = "[/r/{}] {}-{}-{}".format(self.current_subreddit, cdt.year, cdt.month, cdt.day)
				new_playlist_id = self.google_api.create_playlist(playlist_title)

				for song in songs_to_add:
					if song.song_id is not None and song.song_id[0] == "T":
						print ("[/r/{}] Adding {}".format(self.current_subreddit, song.get_search_string()))
						print (vars(song))
						self.google_api.add_songs_to_playlist(new_playlist_id, song.song_id)
					else:
						self.failures.append(song)

				print ("[/r/{}] Making playlist {} public".format(self.current_subreddit, playlist_title))
				self.google_api.edit_playlist(new_playlist_id, public=True)

				share_link = "https://play.google.com/music/playlist/"
				for playlist in self.google_api.get_all_playlists():
					if playlist["id"] == new_playlist_id:
						share_link += playlist["shareToken"]

				print ("[/r/{}] Share link: {}".format(self.current_subreddit, share_link))

				return share_link

			elif len(songs_to_add) > 1000:
				print ("[/r/{}] Processing a multiple playlist upload".format(self.current_subreddit))
				cdt = datetime.datetime.today()
				playlist_title = "[/r/{}] {}-{}-{}".format(self.current_subreddit, cdt.year, cdt.month, cdt.day)
				new_playlists = []
				number_of_playlists = (len(songs_to_add) / config.google_playlist_max_size)
				if len(songs_to_add) % config.google_playlist_max_size != 0:
					number_of_playlists += 1

				for x in range(0, number_of_playlists):
					new_playlist_id = self.google_api.create_playlist(playlist_title)
					new_playlists.append(new_playlist_id)

				for song in songs_to_add:
					self.songs_added_to_current_playlist += 1
					if song.song_id is not None and song.song_id[0] == "T":
						print ("[/r/{}] Adding {}".format(self.current_subreddit, song.get_search_string()))
						print (vars(song))
						playlist_to_add_to = self.songs_added_to_current_playlist / config.google_playlist_max_size
						self.google_api.add_songs_to_playlist(new_playlists[playlist_to_add_to], song.song_id)
					else:
						self.failures.append(song)

				share_links = []

				for new_playlist_id in new_playlists:
					print ("[/r/{}] Making playlist {} public".format(self.current_subreddit, playlist_title))
					self.google_api.edit_playlist(new_playlist_id, public=True)

					share_link = "https://play.google.com/music/playlist/"
					for playlist in self.google_api.get_all_playlists():
						if playlist["id"] == new_playlist_id:
							share_link += playlist["shareToken"]

					print ("[/r/{}] Share link: {}".format(self.current_subreddit, share_link))
					share_links.append(share_link)

				return share_links


		else:
			return config.empty_playlist_link

	def get_id_from_search(self, song_to_search, search_type="song"):
		if search_type == "song":
			print ("[/r/{}] Searching for song".format(self.current_subreddit))
			hits = self.google_api.search(song_to_search.get_search_string())["song_hits"]

			if len(hits) == 1:
				print ("found {} in gplay (1 hit)".format(song_to_search.get_search_string()))
				return hits[0]["track"]["storeId"]
			elif len(hits) > 1:
				best_hit_id = None
				current_name = song_to_search.name
				current_artist = song_to_search.artist

				while best_hit_id is None:
					print ("[/r/{}] Fuzzed-searching for {} {}".format(self.current_subreddit, current_artist, current_name))
					for track in hits:
						track_artist = track["track"]["albumArtist"].encode('utf-8')
						track_name = track["track"]["title"].encode('utf-8')
						track_album = track["track"]["album"].encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, current_artist, current_name, song_to_search.album))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, track_artist, track_name,
														track_album))
						if current_artist == track_artist and \
							current_name == track_name:
							print ("{} in {}".format(song_to_search.get_search_string(), track["track"]))
							best_hit_id = track["track"]["storeId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
					# Start fuzzing the input
					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

					current_name = current_name.split("(feat.")[0].strip() 				# remove remixes / features from song
					for track in hits:
						track_artist = track["track"]["albumArtist"].encode('utf-8')
						track_name = track["track"]["title"].split("(feat.")[0].strip().encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, current_artist, current_name,
																song_to_search.album))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, track_artist, track_name,
																track_album))
						if current_artist == track_artist and \
							current_name == track_name:
							best_hit_id = track["track"]["storeId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					for track in hits:
						track_artist = track["track"]["albumArtist"].encode('utf-8')
						track_name = track["track"]["title"].split("(feat.")[0].strip().encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, current_artist, current_name,
																song_to_search.album))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, track_artist, track_name,
																track_album))
						if current_artist == track_artist and \
							current_name in track_name:
							best_hit_id = track["track"]["storeId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
					# Last try...switch artist and title
					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
					for track in hits:
						track_artist = track["track"]["albumArtist"].encode('utf-8')
						track_name = track["track"]["title"].split("(feat.")[0].strip().encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, current_artist, current_name,
																song_to_search.album))
						print ("[/r/{}] {} - {} from {}".format(self.current_subreddit, track_artist, track_name,
																track_album))
						if current_artist in track_name and \
							current_name in track_artist:
							best_hit_id = track["track"]["storeId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					return config.search_failure_string

				return best_hit_id

			else:
				return config.search_failure_string

		elif search_type == "album":
			print ("[/r/{}] Searching for album".format(self.current_subreddit))
			hits = self.google_api.search(song_to_search.get_album_search_string())["album_hits"]

			if len(hits) == 1:
				print ("found {} in gplay (1 hit)".format(song_to_search.get_album_search_string()))
				return hits[0]["album"]["albumId"]
			elif len(hits) > 1:
				best_hit_id = None
				current_name = song_to_search.album
				current_artist = song_to_search.artist

				while best_hit_id is None:
					print ("searching for {} {}".format(current_artist, current_name))
					for album in hits:
						album_artist = album["album"]["artist"].encode('utf-8')
						album_name = album["album"]["name"].encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {}".format(self.current_subreddit, current_artist, current_name))
						print ("[/r/{}] {} - {}".format(self.current_subreddit, album_artist, album_name))
						if current_artist == album_artist and \
										current_name == album_name:
							best_hit_id = album["album"]["albumId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
					# Start fuzzing the input
					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

					current_name = current_name.split("(")[0].strip()  # remove remixes / features from song
					for album in hits:
						album_artist = album["album"]["artist"].encode('utf-8')
						album_name = album["album"]["name"].encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {}".format(self.current_subreddit, current_artist, current_name))
						print ("[/r/{}] {} - {}".format(self.current_subreddit, album_artist, album_name))
						if current_artist == album_artist and \
										current_name == album_name:
							best_hit_id = album["album"]["albumId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
					# Last try...switch artist and title
					# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
					for album in hits:
						album_artist = album["album"]["artist"].encode('utf-8')
						album_name = album["album"]["name"].encode('utf-8')
						print ("[/r/{}] =-=-=-=-=-=- COMPARING -=-=-=-=-=-=".format(self.current_subreddit))
						print ("[/r/{}] {} - {}".format(self.current_subreddit, current_artist, current_name))
						print ("[/r/{}] {} - {}".format(self.current_subreddit, album_artist, album_name))
						if current_artist == album_name and \
										current_name == album_artist:
							best_hit_id = album["album"]["albumId"]
							print ("Found @ {}".format(best_hit_id))
							return best_hit_id

					return config.search_failure_string

				return best_hit_id

			else:
				return config.search_failure_string

	def parse_youtube_links_from_line(self, comment_line):
		links = []
		while "https://www.youtube.com/" in comment_line:
			# https://www.youtube.com/channel/UCboMX_UNgaPBsUOIgasn3-Q
			if "channel" in comment_line:
				link_index = comment_line.index("https://www.youtube.com/channel")
				link = comment_line[link_index:link_index+56]
				comment_line = comment_line[link_index+56]

			# https://www.youtube.com/playlist?list=PLfdkz2eiSC3a581dIX0xoQmu9te09n5ka
			if "playlist" in comment_line:
				link_index = comment_line.index("https://www.youtube.com/")
				link = comment_line[link_index:link_index+72]
				links.append(link)
				comment_line = comment_line[link_index+72:]

			elif "watch" in comment_line:
				link_index = comment_line.index("https://www.youtube.com/watch")
				link = comment_line[link_index:link_index+43]
				links.append(link)
				comment_line = comment_line[link_index+43:]
		return links

	def parse_spotify_links_from_line(self, comment_line):
		links = []
		while "https://play.spotify.com" in comment_line:
			link_index = comment_line.index("https://play.spotify.com")
			link_substring = comment_line[link_index:]
			if "playlist" in link_substring:
				user_id = link_substring.split("user/")[1].split("/")[0]
				link = comment_line[link_index:link_index + 62 + len(user_id)]
				links.append(link)
				comment_line = comment_line[link_index + 62 + len(user_id):]
			elif "album" in link_substring:
				link = comment_line[link_index:link_index + 53]
				links.append(link)
				comment_line = comment_line[link_index + 53:]
			elif "track" in link_substring:
				link = comment_line[link_index:link_index + 53]
				links.append(link)
				comment_line = comment_line[link_index + 53:]
		return links

	def parse_links_from_comment(self, comment_text):
		parsed_links = []
		lines = comment_text.split("\n\n")
		for idx, dirty_line in enumerate(lines):
			line = dirty_line.encode('utf-8')
			if "spotify.com" in line:
				for parsed_spotify_link in self.parse_spotify_links_from_line(line):
					parsed_links.append(parsed_spotify_link)

			elif "youtube.com" in line:
				for parsed_youtube_link in self.parse_youtube_links_from_line(line):
					parsed_links.append(parsed_youtube_link)

			elif len(line.split("-")) > 1:
				split_line = line.split("-")
				if len(split_line[0]) > 0 and len(split_line[1]) > 0:
					text_link = "text_link|{}|{}".format(split_line[0].strip(), split_line[1].strip())
					parsed_links.append(text_link)

		return parsed_links

	def parse_songs_from_submission(self, submission):
		submission.comments.replace_more()
		songs = []

		for comment in submission.comments.list():
			songs += self.parse_songs_from_comment(comment)

		return songs

	def parse_songs_from_comment(self, comment, scrape_type="track"):
		songs = []

		for link in self.parse_links_from_comment(comment.body):
			scraped_songs = self.songs_from_link(link, scrape_type=scrape_type)
			print ("Songs from comment, post parsed from comment: {}".format(scraped_songs))
			songs += scraped_songs["songs"]

		return songs

	def parse_albums_from_submission(self, submission):
		submission.comments.replace_more()
		songs = []

		for comment in submission.comments.list():
			scraped_songs = self.parse_songs_from_comment(comment, scrape_type="album")
			print ("Albums from sub, post parsed from comment: {}".format(scraped_songs))
			songs += scraped_songs

		return songs

	def post_message_in_thread(self, post, share_link, type="submission"):
		print ("[/r/{}] post_message_in_thread : post {}".format(self.current_subreddit, post))
		print ("[/r/{}] post_message_in_thread : share_link {}".format(self.current_subreddit, share_link))
		print ("[/r/{}] post_message_in_thread : type {}".format(self.current_subreddit, type))
		if share_link != config.empty_playlist_link:
			if type == "submission":
				print ("[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the posted Spotify" \
							" playlist\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "comment":
				print ("[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.submission.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the parent" \
							" comment\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "thread":
				print ("[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.submission.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in this thread" \
							"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "album":
				print (
				"[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the songs in the posted Spotify" \
							" album\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "track":
				print (
				"[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the posted Spotify track" \
							"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "playlist":
				print (
				"[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the posted Spotify playlist" \
							"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "request":
				print (
				"[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.submission.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the requested link" \
							"\n\n[Playlist]({})\n\n{}".format(share_link, config.signature)
				post.reply(post_text)
			elif type == "reddit link error":
				print (
					"[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.submission.url))
				post_text = "Your syntax was incorrect. Check out the github for the command structures" \
							"\n\n{}".format(config.signature)
				post.reply(post_text)
			elif type == "split_playlist":
				print ("[/r/{}] Processing post_message_in_thread {}".format(self.current_subreddit, post.submission.url))
				post_text = "Here is an automatically-generated Google Play Music playlist of the requested link"
				post_text += "Playlist was too long and had to be split up into multiple playlists"
				for idx, playlist_link in enumerate(share_link):
					post_text += "Playlist {}: {}".format(idx, playlist_link)
				post_text += "\n\n{}".format(config.signature)
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
		time_delta = datetime.datetime.now() - self.start_time
		uptime_minutes = divmod(time_delta.total_seconds(), 60)[0]

		message = "**Uptime Statistics for spotplaybot**\n\nspotplaybot has been up for:\n\n" \
				  "{} minutes\n\n{}".format(uptime_minutes, config.signature)

		comment.reply(message)

		print ("[/r/{}] Comment posted!".format(self.current_subreddit))

	def get_parent_comment_links(self, comment):
		print ("[/r/{}] Converting links in parent comment".format(self.current_subreddit))
		comment_parent = comment.parent()
		if hasattr(comment_parent, "replies"):
			post_playlist = self.parse_songs_from_comment(comment_parent)
			post_playlist = self.remove_repeats(post_playlist)
			share_link = self.google_create_playlist(post_playlist)
			self.post_message_in_thread(comment, share_link, type="comment")

			print ("[/r/{}] Complete!".format(self.current_subreddit))
		else:
			print ("Cannot convert a non-comment parent")

	def get_all_thread_track_links(self, comment):
		print ("[/r/{}] Converting links from full submission".format(self.current_subreddit))
		post_playlist = self.parse_songs_from_submission(comment.submission)
		post_playlist = self.remove_repeats(post_playlist)
		share_link = self.google_create_playlist(post_playlist)
		self.post_message_in_thread(comment, share_link, type="thread")

		print ("[/r/{}] Complete".format(self.current_subreddit))

	def convert_comment_link(self, comment):
		print ("[/r/{}] Converting links from comment".format(self.current_subreddit))
		post_playlist = self.parse_songs_from_comment(comment)
		post_playlist = self.remove_repeats(post_playlist)
		share_link = self.google_create_playlist(post_playlist)
		self.post_message_in_thread(comment, share_link, type="request")

	def get_all_thread_album_links(self, comment):
		print ("[/r/{}] Converting links from albums in submission".format(self.current_subreddit))
		if hasattr(comment, "comments"):
			post_playlist = self.parse_albums_from_submission(comment)
			print ("Post parse: {}".format(post_playlist))
			post_playlist = self.remove_repeats(post_playlist)
			print ("Post repeat removal: {}".format(post_playlist))
			share_link = self.google_create_playlist(post_playlist, input_type="searched_songs")
			self.post_message_in_thread(comment, share_link, type="thread")

		else:
			post_playlist = self.parse_albums_from_submission(comment.submission)
			print ("Post parse: {}".format(post_playlist))
			post_playlist = self.remove_repeats(post_playlist)
			print ("Post repeat removal: {}".format(post_playlist))
			share_link = self.google_create_playlist(post_playlist, input_type="searched_songs")
			self.post_message_in_thread(comment, share_link, type="thread")

	def get_all_thread_album_links_at_link(self, comment):
		try:
			print ("[/r/{}] Getting all track links from command {}".format(self.current_subreddit, comment.body))
			reddit_link = comment.body.replace("\n", "").split("convert link thread albums")[1].strip()
			print ("[/r/{}] Reddit link: {}".format(self.current_subreddit, reddit_link))
			reddit_thread = self.reddit.submission(url=reddit_link)
			self.get_all_thread_album_links(reddit_thread)

		except Exception as e:
			raise
			#self.post_message_in_thread(comment, config.search_failure_string, type="reddit link error")

	def get_all_thread_track_links_at_link(self, comment):
		try:
			print ("[/r/{}] Getting all track links from command {}".format(self.current_subreddit, comment.body))
			reddit_link = comment.body.replace("\n", "").split("convert link thread albums")[1].strip()
			print ("[/r/{}] Reddit link: {}".format(self.current_subreddit, reddit_link))
			reddit_thread = self.reddit.submission(url=reddit_link)
			self.get_all_thread_track_links(reddit_thread)

		except Exception as e:
			raise
			#self.post_message_in_thread(comment, config.search_failure_string, type="reddit link error")

	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
	# base methods
	# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

	def process_spotify_threads(self, subreddit):
		for post in self.get_spotify_posts(subreddit):
			post_playlist = self.songs_from_link(post.url)
			share_link = self.google_create_playlist(post_playlist["songs"])
			self.post_message_in_thread(post, share_link, type=post_playlist["type"])

	def process_context_calls(self, subreddit):
		print ("[/r/{}] Searching for context calls".format(self.current_subreddit))
		context_calls = {
			"{} uptime".format(config.context_clue): self.get_uptime,
			"{} convert parent tracks".format(config.context_clue): self.get_parent_comment_links,
			#"{} convert parent albums".format(config.context_clue): self.get_parent_comment_albums,
			"{} convert thread albums".format(config.context_clue): self.get_all_thread_album_links,
			"{} convert thread tracks".format(config.context_clue): self.get_all_thread_track_links,
			"{} convert link comment".format(config.context_clue): self.convert_comment_link,
			"{} convert link thread albums".format(config.context_clue): self.get_all_thread_album_links_at_link,
			"{} convert link thread tracks".format(config.context_clue): self.get_all_thread_track_links_at_link,
		}
		for submission in subreddit.hot(limit=config.post_threshold):
			print "[/r/{}] Searching submission: {}".format(self.current_subreddit, submission.title.encode('utf-8'))
			submission.comments.replace_more()
			for comment in submission.comments.list():
				for context_call in context_calls.keys():
					if context_call in comment.body and not self.previously_processed_comment(comment) and \
						not config.signature in comment.body:
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

	def restart(self):
		self.__init__()

	def run(self):
		"""
		divinity = Song("Divinity", "Porter Robinson")
		song_id = self.get_id_from_search(divinity, type="song")
		track = self.google_api.get_track_info(song_id)
		print ("{} - {} from {}".format(track["albumArtist"], track["title"], track["album"]))
		"""
		failed = False

		while not failed:
			try:
				for subreddit in self.subreddits:
					self.current_subreddit = config.subreddits[self.subreddits.index(subreddit)]
					self.process_spotify_threads(subreddit)
					self.process_context_calls(subreddit)
					print ("[/r/{}] Processing Complete!".format(self.current_subreddit))

			except Exception as e:
				message_body = "Bot is kill.\n{}".format(traceback.format_exc(e))
				print message_body
				failed = True

				message = self.twilio_client.messages.create(to=config.twilio_to_number,
															 from_=config.twilio_from_number,
															 body="{}".format(message_body))

				message2_body = "Trying a restart"
				print message2_body
				message2 = self.twilio_client.messages.create(to=config.twilio_to_number,
															 from_=config.twilio_from_number,
															 body="{}".format(message2_body))
				#self.restart()


def main():
	bot = SpotPlayBot()
	bot.run()


if __name__ == "__main__":
	main()
