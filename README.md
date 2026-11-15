# video_download

Simple command-line video downloader powered by `yt-dlp`, with an optional
tkinter GUI and a PyInstaller-packaged exe for non-technical users.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

ffmpeg is bundled via `imageio-ffmpeg` — no separate install needed.

## CLI usage

The `down` command is defined in `vd.ps1`, which is dot-sourced from the PowerShell
profile (same pattern as `cems.ps1` / `gt.ps1`). It works from any directory in
PowerShell. On a new machine, add this line to `$PROFILE`:

```powershell
. "D:\projects\video_downloader\vd.ps1"
```

```powershell
down "https://www.youtube.com/watch?v=..."   # download video (mp4)
down "URL" -q 720                          # cap quality at 720p
down "URL" -q 0                            # best available (e.g. 4K)
down "URL" --audio-only                    # extract mp3
down "URL1" "URL2"                         # multiple URLs
down "URL" -o D:\videos                    # custom output folder
down --batch urls.txt                      # batch file (one URL per line, # comments)
down "bigbang bang bang bang"              # search YouTube, preview + confirm top result
down "search terms" -y                     # search without the confirm prompt
```

Default quality is **1080p** (`-q` overrides; `-q 0` = best available). If no 1080p
stream exists, the next lower quality is used automatically.

Output defaults to `downloads/` in the project folder.

Without the profile function, run the script directly:

```bash
.venv/Scripts/python.exe download.py "URL" [-q HEIGHT] [--audio-only] [-o DIR] [--batch FILE]
```

Or in PowerShell via `.\dl.ps1 "URL" ...` from the project folder.

## GUI

`vdown` (same `vd.ps1` profile file) opens a tkinter GUI — paste a URL or search
term, pick quality / audio-only / output folder, queue multiple items, and watch
progress. Downloads run on a background thread; the CLI is unaffected.

```powershell
vdown                                # from anywhere, via profile
.venv\Scripts\pythonw.exe gui.py     # directly (pythonw = no console window)
```

## Packaged exe

For friends who shouldn't need Python, build a standalone exe:

```bat
build_exe.bat
```

This installs `pyinstaller` (from `requirements-dev.txt`) and produces:

```
dist\VideoDownloader.exe   (~40-50 MB)
dist\ffmpeg.exe            (~101 MB, loose next to the exe)
```

Share the whole `dist` folder — the exe finds `ffmpeg.exe` beside itself and
falls back to the bundled `imageio-ffmpeg` binary when running unpackaged.

## Files

- `download.py` — CLI core (yt-dlp wrapper); also importable (`download()`, `search()`, `describe_str()`)
- `gui.py` — tkinter GUI front-end
- `vd.ps1` / `dl.ps1` — PowerShell helpers (`down`, `vdown`)
- `build_exe.bat` — PyInstaller build
- `requirements-dev.txt` — build-time deps (pyinstaller)
