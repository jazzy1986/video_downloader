# Video Downloader

A Windows downloader for YouTube and Facebook videos, built on `yt-dlp`. It has a tkinter GUI, a command-line interface, and a PyInstaller build for machines without Python.

Other sites that `yt-dlp` supports should work when given a URL, but only YouTube and Facebook have been tested.

## Setup

Requires Windows and Python 3.12 (the project venv uses 3.12.10).

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

ffmpeg comes bundled through `imageio-ffmpeg`, so no separate install is needed.

## GUI

Open it with `vgui` (see [PowerShell helpers](#powershell-helpers)), or run `.venv\Scripts\pythonw.exe gui.py` from the project folder. `pythonw` opens no console window.

- **URL or search**: paste a URL and press **Add** or Enter. Any other text runs a YouTube search and previews the top result. **Add to Queue** adds the preview to the queue and **Clear** discards it.
- **Queue**: each item has its own progress bar and percentage. **✕** removes an item and **Clear** empties the queue. Both are ignored while a download is running.
- **Quality**: 1080p by default, or 720p, 480p, or Best. **Audio only (mp3)** ignores quality and saves MP3 at 192 kbps.
- **Save to**: defaults to your Downloads folder. **Browse...** picks a folder and remembers it.
- **Download Queue** starts the queue. The status line shows the current file, speed, and ETA, and ends with "Done — all downloads finished". There is no popup on success. **Open folder** opens the save folder.
- If any item fails, a popup lists each URL with its error. Every failure is also written to the log (see [Files and settings](#files-and-settings)).

## Command line

```powershell
vdown "https://www.youtube.com/watch?v=..."   # video, 1080p max
vdown "URL" -q 720                          # cap at 720p
vdown "URL" -q 0                            # best available
vdown "URL" --audio-only                    # mp3
vdown "URL1" "URL2"                         # several URLs
vdown "URL" -o D:\videos                    # output folder
vdown --batch urls.txt                      # one URL per line; # starts a comment
vdown "search terms"                        # YouTube search, asks before downloading
vdown "search terms" -y                     # same, without the prompt
```

Without the PowerShell helpers, run `.venv\Scripts\python.exe download.py` with the same arguments.

| Option | Meaning |
| --- | --- |
| `-q, --quality MAX_HEIGHT` | Maximum video height. Default `1080`; `0` means best available. |
| `--audio-only` | Save audio only, as mp3. |
| `-o, --out DIR` | Output folder. Default `downloads` under the folder you run the command from. |
| `--batch FILE` | Read URLs from a text file, one per line. |
| `-y, --yes` | Skip the confirmation for search terms. |
| `--version` | Print the version. |

Quality notes:
- If a video has nothing at or below the cap, the best available stream is used, which can be higher than the cap.
- If no stream fits the height cap, which is common for portrait videos, the width cap is tried next.
- File names use the video title, truncated to 100 characters.

## PowerShell helpers

`vd.ps1` defines three commands. Add this line to your PowerShell profile so they work from any folder:

```powershell
. "D:\projects\video_downloader\vd.ps1"
```

- `vdown <args>`: runs `download.py` with the project venv.
- `vgui`: opens the GUI.
- `vbuild`: builds the exe (see [Packaged exe](#packaged-exe)).

The paths in `vd.ps1` point to `D:\projects\video_downloader`. Change `$VD_DIR` if the project moves.

`dl.ps1` is a standalone CLI wrapper that doesn't need the profile. Run `.\dl.ps1 "URL"` from the project folder.

## Packaged exe

For machines without Python, run `vbuild`, or run `build_exe.bat` directly. Both need the venv from Setup.

The build installs `pyinstaller` from `requirements-dev.txt` and writes:

```
dist\VideoDownloader.exe   single-file app
dist\ffmpeg.exe            copied beside the exe
```

Share the whole `dist` folder. The exe uses the `ffmpeg.exe` beside it, and falls back to the bundled `imageio-ffmpeg` binary when run unpackaged.

Versioning: the version is stored in `version.json` and appears in the window title and in `--version`. `vbuild` builds with the current version, then bumps the last number for the next build (for example, 1.0.1 becomes 1.0.2). The built exe keeps the version it was built with. If the build fails, the version isn't bumped.

## Files and settings

- `~/.video_downloader.json`: saved save-folder setting (`out_dir`), written when you pick a folder with **Browse...**. `~` is your user folder, such as `C:\Users\<you>`.
- `~/.video_downloader.log`: one entry per failed download, with timestamp, URL, and error.
- `version.json`: app version, bumped by `vbuild`.

Project files:
- `download.py`: CLI and yt-dlp wrapper. It can also be imported. `download()` returns a list of `(url, error)` for failed items, and `search()` and `describe_str()` are also available.
- `gui.py`: tkinter GUI.
- `vd.ps1`, `dl.ps1`: PowerShell helpers.
- `build_exe.bat`: PyInstaller build, run by `vbuild`.
- `VideoDownloader.spec`: generated by PyInstaller on each build.
- `requirements.txt`, `requirements-dev.txt`: runtime and build dependencies.

## Known limitations

- **`Cannot parse data` on Facebook**: some reels fail with this error. They most likely need a Facebook login or aren't available to anonymous visitors. Updating yt-dlp did not fix the reels tested. Login cookies are not supported.
- **Search** uses YouTube only. Other sites need a URL.
- **Site breakage**: when a site stops working, update yt-dlp with `.venv\Scripts\python.exe -m pip install -U yt-dlp`, then rebuild the exe.
