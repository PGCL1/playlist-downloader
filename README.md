# prelude
i find most of my tracks on youtube<br>
i would like to download full playlists on the go<br>
i don't want to have my yt account blocked so the script doesn't use cookies<br>
i aim to run this as part of bigger automation<br>
> :thought_balloon: **my dream:** i like a track on yt, it gets simontaneously downloaded.

# usage
```python
./soundcloud_downloader.py <playlist-url> [desired_downloaded_tracks_amount]
```
- if you're downloading from soundcloud, you can pass this as the `<playlist-url>` param: <br> ```soundcloud.com/<user>/likes```
- don't forget to give the script permissions, ask AI if you don't know :)

# todo 
what is important to me is:
- [x] ensuring audio is the best available quality
- [x] getting the artist cover for the mp3 track
- [x] be able to pass different playlist url as i please
- [x] skips already downloaded tracks across different executions

bonus:
- [x] be able to download from soundcloud 
- [ ] be able to download from bandcamp 

ultra_bonus:
- [ ] be able to download tracks from soulseek

## notes
this command enables me to download a whole youtube playlist
```yt-dlp --cookies-from-browser firefox url``` <br>