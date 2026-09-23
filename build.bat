@echo off
cd /d "%~dp0"
python -m PyInstaller ezzyScrapper.spec --noconfirm
echo.
echo Build finished. Exe is in dist\ezzyScrapper.exe
pause