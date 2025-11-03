@echo off
setlocal

REM This exists only to set the execution policy, so we can
REM then run the powershell .ps1 script, because .bat files suck for scripting
powershell -ExecutionPolicy Bypass -File %~dp0install-visualizers.ps1