@echo off
rem Build VideoDownloader.exe (onefile) and copy ffmpeg.exe next to it.
setlocal
cd /d %~dp0

.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1

rem Delete the spec: PyInstaller regenerates it, so --add-data below is the
rem only reliable way to bundle version.json into the exe.
del /q VideoDownloader.spec 2>nul

.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name VideoDownloader --add-data "version.json;." gui.py
if errorlevel 1 exit /b 1

for /f "delims=" %%f in ('.venv\Scripts\python.exe -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"') do copy /y "%%f" dist\ffmpeg.exe >nul

echo.
echo Built: dist\VideoDownloader.exe + dist\ffmpeg.exe
