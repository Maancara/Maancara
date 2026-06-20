@echo off
REM Ejecuta una revision de precios. Usalo a mano o desde el Programador de tareas (Windows).
cd /d "%~dp0\.."
python -m src.monitor %*
