@REM set HOUDINI_USER_PREF_DIR=C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini.env
for /f "tokens=*" %%a in (C:\Fireflies\Fireflies_BIN\Sidefx\env\houdini.env) do set %%a
@REM set HOUDINI_PATH=C:\Fireflies\Fireflies_BIN\Sidefx
@REM set HOUDINI_TOOLBAR_PATH=C:\Fireflies\Fireflies_BIN\Sidefx\toolbar;&
set HOUDINI_SPLASH_FILE=C:\Fireflies\Fireflies\softs_logo\fireflies_splash_macro.png
set HOUDINI_SPLASH_MESSAFE="COUCOU"
start "" "C:\\Fireflies\\Common\\Houdini_vars\\houdini_205445\\Houdini20.5.445\\bin\\houdini.exe"
