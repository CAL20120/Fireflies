@echo off
setlocal

call %~dp0set_usd_env.bat

call "%USD_INSTALL_DIR%\bin\usdtree.exe" %*

exit /b
