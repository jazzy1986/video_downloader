# Video downloader helpers.
# Load with: . "D:\projects\video_downloader\vd.ps1"
#
#   vdown "https://www.youtube.com/watch?v=..."     - download video (mp4, 1080p default)
#   vdown "URL" -q 720                              - cap quality at 720p
#   vdown "URL" --audio-only                        - extract mp3
#   vdown "URL" -o D:\videos                        - custom output folder
#   vdown "bigbang bang bang bang"                  - search YouTube, preview + confirm top result
#   vgui                                            - open the GUI
#   vbuild                                          - build dist\VideoDownloader.exe, then bump version.json minor

$VD_DIR = "D:\projects\video_downloader"
$VD_VERSION_FILE = Join-Path $VD_DIR "version.json"

function vdown {
    & "$VD_DIR\.venv\Scripts\python.exe" "$VD_DIR\download.py" @args
}

function vgui {
    & "$VD_DIR\.venv\Scripts\pythonw.exe" "$VD_DIR\gui.py"
}

function vbuild {
    & "$VD_DIR\build_exe.bat"
    if ($LASTEXITCODE -ne 0) { return }
    $v = (Get-Content $VD_VERSION_FILE -Raw | ConvertFrom-Json).version
    $p = $v -split '\.'
    if ($p.Count -ne 3) { throw "Unexpected version format: $v" }
    $p[1] = [int]$p[1] + 1
    $p[2] = 0
    $new = $p -join '.'
    @{ version = $new } | ConvertTo-Json | Set-Content $VD_VERSION_FILE
    Write-Host "Version: $v -> $new (next build)"
}
