@echo off
for /f "tokens=*" %%a in (C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini_rm27.env) do set %%a


set "RMANTREE=C:\Program Files\Pixar\RenderManProServer-27.0"


set "DEADLINE_HOU=Z:\Deadline_DB\db_main\submission\Houdini\Client"
set "HOUDINI_ROOT=C:\Fireflies\Common\Houdini_vars\houdini_205445\Houdini20.5.445"


set "PATH=%RMANTREE%\bin;%RMANTREE%\lib;%HOUDINI_ROOT%\bin;%PATH%"

set "PYTHONPATH=%DEADLINE_HOU%;%PYTHONPATH%"

set "HOUDINI_PATH=%RMANTREE%\bin;%DEADLINE_HOU%;%HOUDINI_PATH%;&"

set HOUDINI_SPLASH_FILE=C:\Fireflies\Fireflies\softs_logo\fireflies_splash_rm27.png

"C:\Fireflies\Common\Houdini_vars\houdini_205684\bin\hython.exe" -q %*