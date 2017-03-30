# SpotPlayBot

This project is a bot written in python that scrapes posts in
[reddit.com/r/electronicmusic](https://reddit.com/r/electronicmusic) searching for Spotify
playlists. When it finds a Spotify-hosted playlist, it scrapes the songs from the playlist and re-hosts them on a
Google Play Music playlist.

## Requirements

- [Spotipy](https://github.com/plamere/spotipy) for Spotify API interaction
- [gmusicapi](https://github.com/simon-weber/gmusicapi) as an unofficial Google Play Music API

## Functionality

- Youtube link conversion to google play music

- Text in format ```Artist - Song``` conversion to google play music

- Context-cued functionality

```spotplaybot uptime``` to get the uptime of the bot in seconds

```spotplaybot convert links``` to convert all links in the parent comment

```spotplaybot convert thread``` to convert all links in the thread

## Next Steps

#### Creation of Spotify Playlists from GPlayMusic and Other Sources

Because just because I don't like Spotify doesn't mean that everyone feels that way...

#### Improve searching on google play for songs

A lot of songs are missed because the exact versions posted in the comment is not available on google play,
or due to the fact that the search query is messed up by contextual surrounding text.