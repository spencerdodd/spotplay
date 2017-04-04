# External Libraries
import praw
import spotipy
from gmusicapi import Mobileclient
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOauthError

# Internal Libraries
import config
from botexceptions import AuthorizationError


class Bot:
    def __init__(self):
        self.current_posts = []
        self.processed_posts = []
        self.failed_posts = []
        self.database_location = None

        # APIs
        self.reddit_api = None
        self.gplay_api = None
        self.spotify_api = None
        self.youtube_api = None

        self.authorize_apis()

    def authorize_apis(self):
        """
        This method creates API client objects for the bot to use, utilizing the credentials stored in the config
        file.
        
        :return: AuthorizationError if any of the APIs fail to return an authorized object to use
        """
        # Reddit
        self.reddit_api = praw.Reddit(client_id=config.reddit_id, client_secret=config.reddit_secret,
                                      user_agent=config.user_agent, username=config.reddit_username,
                                      password=config.reddit_password)
        if self.reddit_api.read_only:
            raise AuthorizationError("reddit")

        # Google Play Music
        self.gplay_api = Mobileclient()
        self.gplay_api.login(config.google_email, config.google_password, config.google_device_id)

        if not self.gplay_api.is_authenticated():
            raise AuthorizationError("gplay")

        # Spotify
        try:
            client_credentials_manager = SpotifyClientCredentials(config.spotify_client_id,
                                                                  config.spotify_client_secret)
            self.spotify_api = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        except SpotifyOauthError:
            raise AuthorizationError("spotify")

        # Youtube
        self.youtube_api = build(config.youtube_api_service_name, config.youtube_api_version,
                                 developerKey=config.youtube_api_key)

        print ("[+] Successfully Authorized all APIs")


if __name__ == "__main__":
    bot = Bot()
