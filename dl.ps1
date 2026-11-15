# Simple video downloader wrapper.
# Usage:
#   .\dl.ps1 "https://www.youtube.com/watch?v=..."
#   .\dl.ps1 "URL" -q 720
#   .\dl.ps1 "URL" --audio-only
#   .\dl.ps1 "URL" -o D:\videos

$script = Join-Path $PSScriptRoot "download.py"
& "$PSScriptRoot\.venv\Scripts\python.exe" $script @args
exit $LASTEXITCODE
