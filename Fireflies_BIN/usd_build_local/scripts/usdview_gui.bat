@echo off
setlocal

call "%~dp0set_usd_env.bat"

pushd %~dp0

if "%~1"=="" (
    call "%USD_INSTALL_DIR%\bin\usdview.cmd" "%USD_INSTALL_DIR%\share\usd\tutorials\traversingStage\HelloWorld.usda"
) else (
    call "%USD_INSTALL_DIR%\bin\usdview.cmd" %*
)

popd

exit /b