for /f "tokens=*" %%a in (C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini_rm27.env) do set %%a

set "DEADLINE_HOU=Z:\Deadline_DB\db_main\submission\Houdini\Client"

set PYTHONPATH=%DEADLINE_HOU%;%PYTHONPATH%

set "HOUDINI_PATH=%DEADLINE_HOU%;%HOUDINI_PATH%;&"
set HOUDINI_SPLASH_FILE=C:\Fireflies\Fireflies\softs_logo\fireflies_splash_rm27.png

start "" "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin\\houdini.exe"
