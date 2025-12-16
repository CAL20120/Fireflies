@echo off

set PY="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

set PYTHONPATH=C:\Fireflies\Fireflies_BIN;C:\Fireflies\Fireflies_BIN\usd_build_local\lib\python
set Path=C:\Users\VFX\AppData\Local\Programs\Python\Python310\Scripts\;C:\Users\VFX\AppData\Local\Programs\Python\Python310\;C:\Fireflies\Fireflies_BIN\usd_build_local\bin;C:\Fireflies\Fireflies_BIN\usd_build_local\lib

%PY% "C:\Fireflies\Fireflies_BIN\fireflies\fireflies_utils\usd\fireflies_usd_viewer.py" -asset_path "%~1"

