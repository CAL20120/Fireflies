@echo off
pushd %~dp0

call :ResolvePath USD_PYTHON_DEPS_DIR ../pip-packages
call :ResolvePath USD_PYTHON_DIR ../python

set PATH=^
%USD_PYTHON_DIR%;^
%USD_PYTHON_DEPS_DIR%\bin;^
%PATH%

set PYTHONPATH=%USD_PYTHON_DEPS_DIR%;%PYTHONPATH%

popd

exit /b

:: Resolve path to absolute.
:: Param 1: Name of output variable.
:: Param 2: Path to resolve.
:: Return: Resolved absolute path.
:ResolvePath
    set %1=%~dpfn2
    exit /b
