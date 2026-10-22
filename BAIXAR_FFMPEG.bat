@echo off
setlocal
cd /d "%~dp0"
title WhatsCompress V4 - FFmpeg
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts_baixar_ffmpeg.ps1"
if errorlevel 1 (
 echo.
 echo Falha na verificacao ou no download. Consulte a mensagem acima.
 pause
 exit /b 1
)
echo.
echo Pronto! FFmpeg e FFprobe disponiveis.
pause
exit /b 0
