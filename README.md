# SpotPlayBot

This project is a bot written in python that scrapes posts in
[reddit.com/r/electronicmusic](https://reddit.com/r/electronicmusic) searching for Spotify
playlists and albums. When it finds a Spotify-hosted playlist or album, it scrapes the songs from the playlist and
re-hosts them on a Google Play Music playlist.

The bot also has functionality that can be triggered by comments that contain the keyword ```spotplaybot```

## Requirements

- [spotipy](https://github.com/plamere/spotipy) for Spotify API interaction
- [gmusicapi](https://github.com/simon-weber/gmusicapi) as an unofficial Google Play Music API
- twilio for status updates via SMS
- googleapiclient for interaction with Youtube
- praw for interaction with reddit

## Comment-triggered Functionality

- Youtube link conversion to google play music

- Text in format ```Artist - Song``` conversion to google play music

- Context-cued functionality

```spotplaybot uptime``` to get the uptime of the bot in seconds

```spotplaybot convert parent``` to convert all links in the parent comment

```spotplaybot convert thread``` to convert all links in the thread

```spotplaybot convert link {spotify link}``` to convert the spotify link included in the comment

## Next Steps

- Creation of Spotify Playlists from GPlayMusic and Other Sources

- Improve searching on google play for songs that are missed due to improper parsing from surrounding context when
```Artist - Title``` is placed in the middle of a sentence.