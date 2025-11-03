@echo off
pushd %~dp0

call :ResolvePath USD_INSTALL_DIR ..
call :ResolvePath USD_PYTHON_ENV_SCRIPT set_usd_python_env.bat

if exist %USD_PYTHON_ENV_SCRIPT% (
    call "%USD_PYTHON_ENV_SCRIPT%"
)

:: As of 23.08, there's a bug with how Tf.PreparePythonModule adds entries
:: from the PATH to the list of directories that you can load dll's from -
:: they're added in reverse order.
:: Until there's a fix for that, we add paths before AND after the existing
:: path, to make sure our entries take precedence

set PATH=^
%USD_INSTALL_DIR%\lib;^
%USD_INSTALL_DIR%\plugin\usd;^
%USD_INSTALL_DIR%\bin;^
%PATH%;^
%USD_INSTALL_DIR%\bin;^
%USD_INSTALL_DIR%\plugin\usd;^
%USD_INSTALL_DIR%\lib

set PYTHONPATH=%USD_INSTALL_DIR%\lib\python;%PYTHONPATH%
set PXR_MTLX_STDLIB_SEARCH_PATHS=%USD_INSTALL_DIR%\libraries

popd

exit /b

:: Resolve path to absolute.
:: Param 1: Name of output variable.
:: Param 2: Path to resolve.
:: Return: Resolved absolute path.
:ResolvePath
    set %1=%~dpfn2
    exit /b
