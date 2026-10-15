@echo off
title CAIU A FICHA - resgatar a voz do yovoice
cd /d "%~dp0"

call :achapython
if not defined PY (
  echo.
  echo   [x] Python nao roda. Veja o DIAGNOSTICO.bat.
  echo.
  pause & exit /b 1
)

cls
echo.
echo   RESGATAR A VOZ
echo   ==============
echo.
echo   Pega as falas que voce gerou no yovoice e poe onde o motor
echo   procura. Nao precisa exportar nada no app: os .wav ja estao
echo   salvos em  %%USERPROFILE%%\.yovoice\outputs  desde que foram
echo   gerados.
echo.
echo   Pode rodar quantas vezes quiser. Ele so copia o que achar.
echo.
%PY% "_motor\resgatar_voz.py" %*
echo.
pause
exit /b 0

:achapython
set "PY="
if not exist "_motor\.python.txt" goto detecta
for /f "usebackq tokens=* delims=" %%p in ("_motor\.python.txt") do set "PY=%%p"
if not defined PY goto detecta
%PY% --version >nul 2>&1
if not errorlevel 1 exit /b 0
set "PY="

:detecta
py -3 --version >nul 2>&1 && set "PY=py -3" && exit /b 0
python --version >nul 2>&1 && set "PY=python" && exit /b 0
python3 --version >nul 2>&1 && set "PY=python3" && exit /b 0
exit /b 0
