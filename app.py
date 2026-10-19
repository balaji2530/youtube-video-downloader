#!/usr/bin/env python3
"""
Universal Video Downloader (highest quality)
=============================================

Downloads videos from YouTube, Vimeo, Twitter/X, Facebook, TikTok, Reddit,
and hundreds of other sites supported by yt-dlp, always grabbing the best
available video + audio quality and merging them into a single file.

Requirements:
    pip install -U yt-dlp

Optional but recommended (for merging separate video/audio streams and
re-encoding when needed):
    ffmpeg must be installed and on your PATH.
    - macOS:   brew install ffmpeg
    - Ubuntu:  sudo apt install ffmpeg
    - Windows: https://ffmpeg.org/download.html

Usage:
    python video_downloader.py <URL> [<URL2> ...] [-o OUTPUT_DIR]

Examples:
    python video_downloader.py "https://www.youtube.com/watch?v=XXXXXXXXXXX"
    python video_downloader.py "https://vimeo.com/XXXXXXX" -o ./downloads
    python video_downloader.py url1 url2 url3          # batch download
"""

import argparse
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("yt-dlp is not installed. Install it with:\n    pip install -U yt-dlp")
    sys.exit(1)


def progress_hook(d):
    """Simple progress reporter."""
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        filename = Path(d.get("filename", "")).name
        print(f"\r  {filename}: {pct} at {speed}, ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\n  Download finished, now post-processing (merging/converting)...")


def build_ydl_opts(output_dir: str) -> dict:
    """
    Build yt-dlp options that:
      - Pick the best video and best audio streams independently
        (bestvideo+bestaudio), falling back to the single best combined
        stream if separate streams aren't available.
      - Prefer mp4/m4a to maximize compatibility, but will fall back to
        the highest quality regardless of container if needed.
      - Merge into a single .mp4 file using ffmpeg.
    """
    output_template = str(Path(output_dir) / "%(title).200s [%(id)s].%(ext)s")

    ydl_opts = {
        # Try best mp4 video + best m4a audio first, then fall back to
        # the overall best video+audio, then best single format available.
        "format": (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
            "bestvideo*+bestaudio/"
            "best"
        ),
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "progress_hooks": [progress_hook],
        "noplaylist": True,      # set True if you only want a single video, not a whole playlist
        "quiet": False,
        "no_warnings": False,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        # Embed metadata + thumbnail when possible
        "writethumbnail": False,
        "postprocessor_args": {
            "ffmpeg": ["-movflags", "+faststart"],
        },
    }
    return ydl_opts


def download_video(url: str, output_dir: str) -> bool:
    print(f"\n=== Downloading: {url} ===")
    ydl_opts = build_ydl_opts(output_dir)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "unknown title")
            print(f"\n  Saved: {title}")
            return True
    except yt_dlp.utils.DownloadError as e:
        print(f"\n  Failed to download {url}: {e}")
        return False
    except Exception as e:
        print(f"\n  Unexpected error for {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download videos in the highest available quality from any yt-dlp-supported platform."
    )
    parser.add_argument("urls", nargs="+", help="One or more video URLs to download")
    parser.add_argument(
        "-o", "--output", default="./downloads",
        help="Output directory (default: ./downloads)"
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for url in args.urls:
        success = download_video(url, str(output_dir))
        results.append((url, success))

    print("\n=== Summary ===")
    for url, success in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {url}")

    failed = sum(1 for _, s in results if not s)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()




    #  python video_downloader.py "https://www.youtube.com/shorts/a8F_vTkj7-I?feature=share"