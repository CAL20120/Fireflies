@echo off

set PY="%LOCALAPPDATA%\Programs\Python\Python310\python.exe"

%PY% "C:\Fireflies\Fireflies_BIN\fireflies\fireflies_utils\usd\local_tx_make.py" -input_file "%~1"