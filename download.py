"""Simple video downloader powered by yt-dlp.

Usage:
    python download.py <url> [url ...]
    python download.py <url> --audio-only        # extract audio as mp3
    python download.py <url> -o D:/videos        # output directory
    python download.py --batch urls.txt          # read urls from a file
"""

import argparse
import sys

if sys.stdout is not None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr is not None:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

import imageio_ffmpeg
from yt_dlp import YoutubeDL

__version__ = "1.0.0"


def find_ffmpeg():
    """Locate ffmpeg: a loose ffmpeg.exe beside a packaged exe wins,
    otherwise fall back to the imageio-ffmpeg bundled binary."""
    if getattr(sys, "frozen", False):
        sibling = Path(sys.executable).parent / "ffmpeg.exe"
        if sibling.exists():
            return str(sibling)
    return imageio_ffmpeg.get_ffmpeg_exe()


class Logger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        if "JavaScript runtime" not in msg:
            print(msg, file=sys.stderr)

    def error(self, msg):
        print(msg, file=sys.stderr)


def describe_str(info):
    dur = info.get("duration")
    dur_str = f"{dur // 60}:{dur % 60:02d}" if dur else "?"
    views = info.get("view_count")
    views_str = f"{views:,}" if views else "?"
    who = info.get("uploader") or info.get("channel") or info.get("channel_id") or "?"
    return f"{info.get('title', '?')}\n{who} | {dur_str} | {views_str} views"


def describe(info):
    print(f"  {describe_str(info).replace(chr(10), chr(10) + '  ')}")


def confirm(ydl, query, assume_yes):
    info = ydl.extract_info(f"ytsearch5:{query}", download=False)
    entries = list(info.get("entries") or [])
    entry = next((e for e in entries if "watch?v=" in (e.get("url") or "")), None)
    if not entry:
        print("  no video found in search results")
        return None
    describe(entry)
    try:
        ans = input("  Download? [Y/n] ").strip().lower()
    except EOFError:
        return None
    if assume_yes or ans != "n":
        return entry.get("url")
    return None


def build_opts(out_dir="downloads", audio_only=False, quality=None,
               progress_hook=None):
    opts = {
        "outtmpl": str(Path(out_dir) / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "extract_flat": True,
        "quiet": True,
        "logger": Logger(),
        "progress_hooks": [progress_hook or cli_progress_hook],
        "postprocessors": [],
        "ffmpeg_location": find_ffmpeg(),
    }

    if audio_only:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"].append({
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        })
    else:
        q = 1080 if quality is None else quality
        opts["format"] = ("bestvideo+bestaudio/best" if q == 0 else
                          f"bestvideo[height<={q}]+bestaudio/best[height<={q}]")
        opts["merge_output_format"] = "mp4"
    return opts


def search(query, limit=5):
    """Return yt-dlp search entries for a query (no download)."""
    with YoutubeDL({"quiet": True, "extract_flat": True, "logger": Logger()}) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    return list(info.get("entries") or [])


def download(urls, out_dir="downloads", audio_only=False, quality=None,
             assume_yes=False, progress_hook=None):
    opts = build_opts(out_dir, audio_only, quality, progress_hook)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    failed = []
    with YoutubeDL(opts) as ydl:
        for url in urls:
            try:
                if not url.startswith(("http://", "https://")):
                    url = confirm(ydl, url, assume_yes)
                    if not url:
                        print("  skipped\n")
                        continue
                ydl.download([url])
            except Exception as e:
                print(f"\nFAILED: {url} ({e})")
                failed.append(url)
    return failed


def cli_progress_hook(d):
    if d["status"] == "downloading":
        pct = d.get("_percent_str", "?").strip()
        spd = d.get("_speed_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        print(f"\r  {pct} @ {spd} ETA {eta}   ", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  done -> {d['filename']}")


def main():
    p = argparse.ArgumentParser(description="Download videos with yt-dlp")
    p.add_argument("--version", action="version",
                   version=f"%(prog)s {__version__}")
    p.add_argument("urls", nargs="*",
                   help="video URL(s), or a search term (non-URL input searches YouTube)")
    p.add_argument("--batch", metavar="FILE", help="text file with one URL per line")
    p.add_argument("-o", "--out", default="downloads", help="output directory")
    p.add_argument("--audio-only", action="store_true", help="extract audio as mp3")
    p.add_argument("-q", "--quality", type=int, metavar="MAX_HEIGHT",
                   help="max video height (default 1080; 0 = best available)")
    p.add_argument("-y", "--yes", action="store_true",
                   help="skip the confirm prompt for search terms")
    args = p.parse_args()

    urls = list(args.urls)
    if args.batch:
        urls += [l.strip() for l in Path(args.batch).read_text().splitlines()
                 if l.strip() and not l.startswith("#")]
    if not urls:
        p.error("no URLs given (pass URLs as arguments or use --batch)")

    failed = download(urls, args.out, args.audio_only, args.quality, args.yes)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
