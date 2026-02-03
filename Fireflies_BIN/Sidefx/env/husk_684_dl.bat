@echo off
for /f "tokens=*" %%a in (C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini_rm27.env) do set %%a

set "HOUDINI_USER_PREF_DIR=C:\Fireflies\Fireflies_BIN\Sidefx\env"

set "RMANTREE=C:\Program Files\Pixar\RenderManProServer-27.1"


set "DEADLINE_HOU=Z:\Deadline_DB\db_main\submission\Houdini\Client"
set "HOUDINI_ROOT=C:\Fireflies\Common\Houdini_vars\houdini_205684


set "PATH=%RMANTREE%\bin;%RMANTREE%\lib;%HOUDINI_ROOT%\bin;%PATH%"

set "PYTHONPATH=%DEADLINE_HOU%;%PYTHONPATH%"

set "HOUDINI_PATH=%RMANTREE%\bin;%DEADLINE_HOU%;%HOUDINI_PATH%;&"


"C:\Fireflies\Common\Houdini_vars\houdini_205684\bin\husk.exe" %*