@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
if exist "D:\pyenv\kaoyan\Scripts\python.exe" (
  "D:\pyenv\kaoyan\Scripts\python.exe" "%~dp0bootstrap_env.py" %*
) else (
  python "%~dp0bootstrap_env.py" %*
)
pause
