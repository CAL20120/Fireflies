@echo off
for /f "tokens=*" %%a in (C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini_rm27.env) do set %%a

set "HOUDINI_USER_PREF_DIR=C:\Fireflies\Fireflies_BIN\Sidefx\env"

set "RMANTREE=C:\Program Files\Pixar\RenderManProServer-27.0"


set "DEADLINE_HOU=\\CHRIS_NAS\Deadline_DB\db_main\submission\Houdini\Client"
set "HOUDINI_ROOT=C:\Fireflies\Common\Houdini_vars\houdini_205445\Houdini20.5.445"


set "PATH=%RMANTREE%\bin;%RMANTREE%\lib;%HOUDINI_ROOT%\bin;%PATH%"

set "PYTHONPATH=%DEADLINE_HOU%;%PYTHONPATH%"

set "HOUDINI_PATH=%RMANTREE%\bin;%DEADLINE_HOU%;%HOUDINI_PATH%;&"


"C:\Fireflies\Common\Houdini_vars\houdini_205445\Houdini20.5.445\bin\husk.exe" %*