for /f "tokens=*" %%a in (C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini_rm27.env) do set %%a

set "DEADLINE_HOU=Z:\Deadline_DB\db_main\submission\Houdini\Client"

set PYTHONPATH=%DEADLINE_HOU%;%PYTHONPATH%

set "HOUDINI_PATH=%DEADLINE_HOU%;%HOUDINI_PATH%;&"
set HOUDINI_SPLASH_FILE=C:\Fireflies\Fireflies\softs_logo\houdini_splashscreen_loewe.png

start "" "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205684\\bin\\houdini.exe"