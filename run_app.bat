@echo off
REM ===========================================================
REM  Stock screener dashboard launcher (localhost only)
REM  Usage: double-click this file.
REM   - A console window opens; the browser opens shortly after.
REM   - To stop: close this window, or press Ctrl+C here.
REM  (ASCII-only on purpose: .bat files are read in the OEM
REM   codepage, so Korean text here would be garbled.)
REM ===========================================================

cd /d "%~dp0"
set PYTHONUTF8=1

REM Load the fresh daily-scanned candidates (KR + US) from the cloud data branch
REM so a double-click always shows the latest snapshot without a local scan.
REM (You can still switch to "live scan" in the sidebar.)
set SNAPSHOT_URL=https://raw.githubusercontent.com/mechanic-eee/stock-screener/data/candidates.parquet

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv not found. Run these once first:
  echo    python -m venv .venv
  echo    .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)

echo Starting screener dashboard... opening http://localhost:8501
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false

echo.
echo Server stopped.
pause
