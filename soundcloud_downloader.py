#!/usr/bin/env python3

import os
import json
import sys
import yt_dlp
from yt_dlp.utils import DownloadCancelled

def make_stable_key(info: dict) -> str:
    """
    Stable key across runs. Works both for full info_dict and extract_flat entries.
    """
    extractor = (
        info.get("extractor_key")
        or info.get("extractor")
        or info.get("ie_key")      # important for extract_flat entries
        or "unknown"
    ).lower()

    item = (
        info.get("id")
        or info.get("webpage_url")
        or info.get("url")         # important for extract_flat entries
        or info.get("original_url")
        or "unknown"
    )

    return f"{extractor}:{item}"

def load_seen_keys(path: str) -> set:
    seen = set()
    if not os.path.exists(path):
        return seen
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                key = obj.get("key")
                if key:
                    seen.add(key)
            except json.JSONDecodeError:
                pass
    return seen

def append_seen_record(path: str, info: dict) -> None:
    rec = {
        "key": make_stable_key(info),
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "webpage_url": info.get("webpage_url"),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def filter_duration(info: dict, max_seconds: int = 900):
    dur = info.get("duration") or 0
    if dur > max_seconds:
        return "Skipping track longer than 15 minutes"
    return None

def precheck_duplicates(url: str, seen_keys: set, scan_opts: dict) -> dict:
    """
    preflight scan: counts how many entries are new vs already seen,
    and how many duplicates appear inside the list itself.
    """
    total = 0
    already_seen = 0
    new_items = 0
    duplicates_in_list = 0

    in_list_keys = set()

    with yt_dlp.YoutubeDL(scan_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        entries = info.get("entries")
        if entries is None:
            entries = [info]

        for e in entries:
            if not e:
                continue

            total += 1
            key = make_stable_key(e)

            if key in in_list_keys:
                duplicates_in_list += 1
                continue
            in_list_keys.add(key)

            if key in seen_keys:
                already_seen += 1
            else:
                new_items += 1

    return {
        "total": total,
        "already_seen": already_seen,
        "new_items": new_items,
        "duplicates_in_list": duplicates_in_list,
    }

def download_likes(url: str, new_song_limit: int, output_dir: str = "downloads"):
    os.makedirs(output_dir, exist_ok=True)

    seen_path = os.path.join(output_dir, "seen.jsonl")
    log_file = os.path.join(output_dir, "download_log.txt")
    error_log_file = os.path.join(output_dir, "download_log_ERROR.txt")

    seen_keys = load_seen_keys(seen_path)
    new_downloads = {"count": 0}

    # ---- precheck (no download) ----
    scan_opts = {
        "remote_components": {"ejs:github"},
        # only needed if you wanna download private videos
        # i don't and don't wanna my account blocked
        # "cookiesfrombrowser": ("firefox",),
        "skip_download": True,
        "extract_flat": True,
        "ignoreerrors": True,
        "quiet": True,
        "no_warnings": True,
    }

    stats = precheck_duplicates(url, seen_keys, scan_opts)
    print(
        f"Precheck: total={stats['total']} | new={stats['new_items']} | "
        f"already_seen={stats['already_seen']} | duplicates_in_list={stats['duplicates_in_list']}"
    )

    if stats["new_items"] == 0:
        print("Nothing new to download. Exiting.")
        return

    # ---- Hooks ----
    def progress_hook(d):
        if d.get("status") == "error":
            info = d.get("info_dict") or {}
            title = info.get("title") or "Unknown"
            err = d.get("error") or "Unknown error"
            with open(error_log_file, "a", encoding="utf-8") as f:
                f.write(f"{title} - {err}\n")

    def postprocessor_hook(d):
        # mark as seen only after postprocessing (MP3 conversion) finishes
        if d.get("status") != "finished":
            return

        info = d.get("info_dict") or {}
        if not info:
            return

        # duration filter needs full info (works fine here too)
        if filter_duration(info):
            return

        key = make_stable_key(info)
        if key in seen_keys:
            return

        seen_keys.add(key)
        append_seen_record(seen_path, info)

        title = info.get("title") or "Unknown"
        uploader = info.get("uploader") or info.get("channel") or "Unknown"
        line = f"{title} - {uploader} ({key})"
        print(f"✅ Saved: {line}")

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        new_downloads["count"] += 1
        if new_song_limit and new_downloads["count"] >= new_song_limit:
            raise DownloadCancelled(f"Reached new_song_limit={new_song_limit}")

    # ---- Real download opts (MP3 output) ----
    ydl_opts = {
        "remote_components": {"ejs:github"},

        # best available source, then convert to MP3 for Traktor
        "format": "bestaudio/best",
        "sleep_requests": 1.0,        # pause between extraction HTTP requests
        "sleep_interval": 2.0,        # pause before each download
        "max_sleep_interval": 6.0,    # randomize sleep_interval up to this
        "ratelimit": 2_000_000,       # bytes/sec (≈ 2 MB/s)  (CLI: --limit-rate)
        "concurrent_fragment_downloads": 1,  # don’t hammer HLS/DASH with parallel fragments

        # single folder only
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        "restrictfilenames": True,
        "windowsfilenames": True,

        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"},
            {"key": "EmbedThumbnail"},
            {"key": "FFmpegMetadata"},
        ],
        "writethumbnail": True,
        "keepthumbnail": False,

        "ignoreerrors": True,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],

        # skip duplicates early during the run too
        "match_filter": lambda info: filter_duration(info) or (
            f"Skipping (already downloaded): {make_stable_key(info)}"
            if make_stable_key(info) in seen_keys else None
        ),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except DownloadCancelled as e:
        print(str(e))
    except Exception as e:
        print(f"Download error: {e}")

# ---------- CLI ----------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_all_likes_from_soundcloud.py <likes_url> [new_song_limit]")
        sys.exit(1)

    likes_url = sys.argv[1]
    new_song_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0  # 0 = no limit
    download_likes(likes_url, new_song_limit)