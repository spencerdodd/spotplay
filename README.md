# SpotPlay

This project is a bot written in python that scrapes posts in
[reddit.com/r/electronicmusic](https://reddit.com/r/electronicmusic) searching for Spotify
playlists. When it finds a Spotify-hosted playlist, it scrapes the songs from the playlist and re-hosts them on a
Google Play Music playlist.

## Requirements

- [Spotipy](https://github.com/plamere/spotipy) for Spotify API interaction
- [gmusicapi](https://github.com/simon-weber/gmusicapi) as an unofficial Google Play Music API

## Next Steps

#### Youtube to GPlayMusic Conversion Functionality

Pretty self-explanatory. Work from straight links so that it can be used for parsing links in threads into a single
playlist compilation

#### Context-dependent Functionality

Integrate a comment-cue that will trigger functions. i.e. ("spotplay convert thread") that would read all links in the
thread and convert/compile them into Spotify/GPlayMusic playlists.

#### Creation of Spotify Playlists from GPlayMusic and Other Sources

Because just because I don't like Spotify doesn't mean that everyone feels that way...