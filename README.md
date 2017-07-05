# SpotPlayBot

This project is a bot written in python that scrapes posts in
[reddit.com/r/electronicmusic](https://reddit.com/r/electronicmusic) searching for Spotify
playlists and albums. When it finds a Spotify-hosted playlist or album, it scrapes the songs from the playlist and
re-hosts them on a Google Play Music playlist.

The bot also has functionality that can be triggered by comments that contain the keyword ```spotplaybot```.

## Requirements

Spotify account
Google Play music account
Google account (^ can be same)
Reddit account

## Installation
```
git clone https://github.com/spencerdodd/spotplaybot
cd spotplaybot
pip install -r requirements.txt
...
[replace config.py with your data]
...
cd spotplaybot
python bot.py
```

## Libraries

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


```
[/r/spotplaybot] =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=Failures=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
[/r/spotplaybot] 0: Wurlitzer The Lushlife Project : {'album': 'Budapest Eskimos', 'song_id': 'search failure...could not locate song', 'name': 'Wurlitzer', 'artist': 'The Lushlife Project'}
[/r/spotplaybot] 1: Lifespan - Instrumental Vaults : {'album': 'Lifespan', 'song_id': 'search failure...could not locate song', 'name': 'Lifespan - Instrumental', 'artist': 'Vaults'}
[/r/spotplaybot] 2: Fleur Blanche Orsten : {'album': 'Cutworks', 'song_id': 'search failure...could not locate song', 'name': 'Fleur Blanche', 'artist': 'Orsten'}
[/r/spotplaybot] 3: Marbles & Drains TM Juke : {'album': 'Renommee Recommends...', 'song_id': 'search failure...could not locate song', 'name': 'Marbles & Drains', 'artist': 'TM Juke'}
[/r/spotplaybot] 4: Body Language - Interpretation Booka Shade : {'album': 'Movements', 'song_id': 'search failure...could not locate song', 'name': 'Body Language - Interpretation', 'artist': 'Booka Shade'}
[/r/spotplaybot] 5: Mr. Handagote Tomáš Dvořák : {'album': 'Machinarium Soundtrack', 'song_id': 'search failure...could not locate song', 'name': 'Mr. Handagote', 'artist': 'Tom\xc3\xa1\xc5\xa1 Dvo\xc5\x99\xc3\xa1k'}
[/r/spotplaybot] 6: Adagio Sostenuto Orsten : {'album': 'Cutworks', 'song_id': 'search failure...could not locate song', 'name': 'Adagio Sostenuto', 'artist': 'Orsten'}
[/r/spotplaybot] 7: Nitro - R.I.P. Nujabes Mix AGQ : {'album': 'Tribute To Jun 2 (Nujabes Tribute)', 'song_id': 'search failure...could not locate song', 'name': 'Nitro - R.I.P. Nujabes Mix', 'artist': 'AGQ'}
```