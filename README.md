# Prelude
i find most of my tracks on youtube<br>
i would like to download full playlists on the go<br>
i don't want to have my yt account blocked so the script doesn't use cookies<br>
i aim to run this as part of bigger automation<br>
> :thought_balloon: **My Dream:** I like a track on yt, it gets simontaneously downloaded.

# Usage
```python
./soundcloud_downloader.py <playlist-url> [desired_amount_of_downloaded_tracks]
```
- if you're downloading from soundcloud, you can pass this as the `<playlist-url>` param: ```soundcloud.com/<user>/likes```

# Todo 
what is important to me is:
- [X] ensuring audio is the best available quality
- [X] getting the artist cover for the mp3 track
- [X] be able to pass different playlist url as i please
- [X] skips already downloaded tracks across different executions

BONUS:
- [X] be able to download from soundcloud 
- [ ] be able to download from bandcamp 

ULTRA_BONUS:
- [ ] be able to download tracks from Soulseek

## Notes
this command enables me to download a whole youtube playlist
```yt-dlp --cookies-from-browser firefox URL``` <br>