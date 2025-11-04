@echo off

set PY="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

%PY% "C:\Fireflies\Fireflies_BIN\fireflies\fireflies_utils\usd\fireflies_usd_viewer.py" -asset_path "%~1"