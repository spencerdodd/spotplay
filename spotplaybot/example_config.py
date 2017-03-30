# Reddit configs
subreddits = [
	"spotplaybot",
	"electronicmusic"
]
reddit_id = ""
reddit_secret = ""
reddit_username = ""
reddit_password = ""
user_agent = "SpotPlay Bot 0.1"

# Spotipy configs
spotify_client_id = ""
spotify_client_secret = ""

# gmusicapi configs
google_email = ""
google_password = ""

# twilio configs
twilio_account_sid = ""
twilio_auth_token = ""
twilio_to_number = ""
twilio_from_number = ""

# youtube configs
youtube_api_service_name = "youtube"
youtube_api_version = "v3"
youtube_api_key = ""


# spotplaybot configs
context_clue = "spotplaybot"
github_url = "https://github.com/spencerdodd/spotplaybot"
contact_username = "/u/aztechk"
signature = 		"I am a bot, this was performed automatically.\n" \
					"If there is a problem with this post, please contact {}\n\n" \
				   	"*-your friendly neighborhood spotplaybot*\n\n" \
					"---------------------\n\n" \
					"^Source ^code: ^[Github]({})".format(contact_username, github_url)
search_failure_string = "search failure...could not locate song"
post_threshold = 100