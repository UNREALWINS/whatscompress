@echo off
setlocal
cd /d "%~dp0"
title WhatsCompress V4 - Gerar portatil para Windows

call :python
if not defined PYTHON (
 echo ERRO: Python nao encontrado. Verifique a instalacao neste computador.
 pause
 exit /b 1
)

echo Usando: %PYTHON%
echo.
echo Verificando FFmpeg local...
if not exist "bin\ffmpeg.exe" goto missing_ffmpeg
if not exist "bin\ffprobe.exe" goto missing_ffmpeg
"bin\ffmpeg.exe" -version >nul 2>&1
if errorlevel 1 goto missing_ffmpeg
"bin\ffprobe.exe" -version >nul 2>&1
if errorlevel 1 goto missing_ffmpeg
goto deps

:missing_ffmpeg
echo FFmpeg nao instalado na pasta bin. Execute BAIXAR_FFMPEG.bat primeiro.
pause
exit /b 1

:deps
echo Instalando bibliotecas SOMENTE neste computador para gerar o EXE...
"%PYTHON%" -m pip install --upgrade PySide6 pyinstaller
if errorlevel 1 (
 echo ERRO ao instalar dependencias.
 pause
 exit /b 1
)
echo.
echo Compilando WhatsCompress.exe...
"%PYTHON%" -m PyInstaller --noconfirm --clean --onedir --windowed --name WhatsCompress --contents-directory _internal whatscompress.py
if errorlevel 1 (
 echo ERRO durante compilacao.
 pause
 exit /b 1
)

if not exist "dist\WhatsCompress\bin" mkdir "dist\WhatsCompress\bin"
copy /y "bin\ffmpeg.exe" "dist\WhatsCompress\bin\ffmpeg.exe" >nul
copy /y "bin\ffprobe.exe" "dist\WhatsCompress\bin\ffprobe.exe" >nul
if not exist "dist\WhatsCompress\WhatsCompress.exe" goto failed
if not exist "dist\WhatsCompress\bin\ffmpeg.exe" goto failed
if not exist "dist\WhatsCompress\bin\ffprobe.exe" goto failed
copy /y "LEIA-ME.txt" "dist\WhatsCompress\LEIA-ME.txt" >nul

echo.
echo Criando ZIP portatil...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -LiteralPath 'dist\WhatsCompress' -DestinationPath 'WhatsCompress_V4_PORTABLE_WINDOWS.zip' -CompressionLevel Optimal -Force"
if errorlevel 1 goto failed

echo.
echo === COMPILACAO CONCLUIDA ===
echo Aplicativo: dist\WhatsCompress\WhatsCompress.exe
echo Pacote para ela: WhatsCompress_V4_PORTABLE_WINDOWS.zip
echo Ela NAO precisara instalar Python.
pause
exit /b 0

:failed
echo ERRO: verificacao do pacote final falhou.
pause
exit /b 1

:python
if exist "C:\Python314\python.exe" (
 set "PYTHON=C:\Python314\python.exe"
 exit /b
)
if exist "%LocalAppData%\Programs\Python\Python314\python.exe" (
 set "PYTHON=%LocalAppData%\Programs\Python\Python314\python.exe"
 exit /b
)
if exist "%LocalAppData%\Programs\Python\Python310\python.exe" (
 set "PYTHON=%LocalAppData%\Programs\Python\Python310\python.exe"
 exit /b
)
for /f "delims=" %%P in ('where python.exe 2^>nul') do (
 if not defined PYTHON if exist "%%P" set "PYTHON=%%P"
)
exit /b
