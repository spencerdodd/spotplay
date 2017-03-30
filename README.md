# SpotPlay

This project is a bot written in python that scrapes posts in
[reddit.com/r/electronicmusic](https://reddit.com/r/electronicmusic) searching for Spotify
playlists. When it finds a Spotify-hosted playlist, it scrapes the songs from the playlist and re-hosts them on a
Google Play Music playlist.

## Requirements

- [Spotipy](https://github.com/plamere/spotipy) for Spotify API interaction
- [gmusicapi](https://github.com/simon-weber/gmusicapi) as an unofficial Google Play Music API

## Next Steps

---

#### Context-dependent functionality

Integrate a comment-cue that will trigger functions. i.e. ("spotplay convert thread") that would read all links in the
thread and convert/compile them into Spotify/GPlayMusic playlists.