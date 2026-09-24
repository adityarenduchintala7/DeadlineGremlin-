@echo off
setlocal
set PYTHONIOENCODING=utf-8
python "%~dp0taskchecker\main.py" %*
endlocal
