@echo off
setlocal
cd /d "%~dp0"
title WhatsCompress V4 - Teste
call :python
if not defined PYTHON (
 echo ERRO: Python nao localizado.
 echo Instale Python ou use C:\Python314\python.exe.
 pause
 exit /b 1
)
"%PYTHON%" -c "import PySide6" >nul 2>&1
if errorlevel 1 (
 echo PySide6 nao encontrado. Tentando instalar...
 "%PYTHON%" -m pip install PySide6
 if errorlevel 1 (echo ERRO: Falha na instalacao do PySide6. & pause & exit /b 1)
)
"%PYTHON%" whatscompress.py
if errorlevel 1 (echo. & echo O WhatsCompress apresentou um erro. & pause & exit /b 1)
exit /b 0

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
