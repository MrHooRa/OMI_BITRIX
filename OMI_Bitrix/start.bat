@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv
  if errorlevel 1 goto :failed
)
.venv\Scripts\python.exe -c "import flask, tzdata, waitress, sentence_transformers, sklearn, torch" >nul 2>&1
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements-lock.txt
  if errorlevel 1 goto :failed
)
.venv\Scripts\python.exe serve.py
exit /b %errorlevel%
:failed
echo Installation failed. See docs\admin-guide.md for Python version and offline wheels.
pause
exit /b 1
