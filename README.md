# SpotPlayBot

This project is a bot written in python that scrapes posts in
[reddit.com/r/electronicmusic](https://reddit.com/r/electronicmusic) searching for Spotify
playlists and albums. When it finds a Spotify-hosted playlist or album, it scrapes the songs from the playlist and
re-hosts them on a Google Play Music playlist.

The bot also has functionality that can be triggered by comments that contain the keyword ```spotplaybot```.

## Requirements

- [spotipy](https://github.com/plamere/spotipy) for Spotify API interaction
- [gmusicapi](https://github.com/simon-weber/gmusicapi) as an unofficial Google Play Music API
- twilio for status updates via SMS
- googleapiclient for interaction with Youtube
- praw for interaction with reddit

## Comment-triggered Functionality

- Youtube/Spotify link conversion to google play music

- Text in format ```Artist - Song``` conversion to google play music

- Context-cued functionality

```spotplaybot uptime``` to get the uptime of the bot in seconds (maybe...)

```spotplaybot convert parent tracks``` to get a playlist of all the songs in the parent comment

```spotplaybot convert thread tracks``` to get a playlist of all of the songs in the entire thread

```spotplaybot convert thread albums``` to get a playlist of all the songs in all the albums in the entire thread

```spotplaybot convert link comment {{link}}``` to get a playlist of the songs in the given link

```spotplaybot convert link thread albums {{reddit-link}}``` to get a playlist of all the songs in all the
albums in a linked reddit thread

```spotplaybot convert link thread tracks {{reddit-link}}``` to get a playlist of all the songs in a
linked reddit thread

## Next Steps

- Convert parent comment albums to playlists

- Creation of Spotify Playlists from GPlayMusic and Other Sources

- Improve searching on google play for songs that are missed due to improper parsing from surrounding context when
```Artist - Title``` is placed in the middle of a sentence.