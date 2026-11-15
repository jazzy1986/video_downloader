# Video downloader helpers.
# Load with: . "D:\projects\video_downloader\vd.ps1"
#
#   down "https://www.youtube.com/watch?v=..."     - download video (mp4, 1080p default)
#   down "URL" -q 720                              - cap quality at 720p
#   down "URL" --audio-only                        - extract mp3
#   down "URL" -o D:\videos                        - custom output folder
#   down "bigbang bang bang bang"                  - search YouTube, preview + confirm top result
#   vdown                                           - open the GUI

function down {
    & "D:\projects\video_downloader\.venv\Scripts\python.exe" "D:\projects\video_downloader\download.py" @args
}

function vdown {
    & "D:\projects\video_downloader\.venv\Scripts\pythonw.exe" "D:\projects\video_downloader\gui.py"
}
