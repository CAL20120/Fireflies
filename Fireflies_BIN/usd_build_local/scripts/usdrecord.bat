@echo off
setlocal

call %~dp0set_usd_env.bat

call "%USD_INSTALL_DIR%\bin\usdrecord.cmd" %*

exit /b
