@echo off
REM ===========================================================
REM  폭락주 스크리너 대시보드 실행 (localhost 전용)
REM  사용법: 이 파일을 더블클릭하면 됩니다.
REM  - 검은 창이 뜨고 잠시 후 브라우저가 자동으로 열립니다.
REM  - 끄려면: 그 검은 창을 닫거나, 창에서 Ctrl+C 를 누르세요.
REM ===========================================================

cd /d "%~dp0"
set PYTHONUTF8=1

if not exist ".venv\Scripts\python.exe" (
  echo [오류] .venv 가 없습니다. 먼저 아래를 한 번 실행하세요:
  echo    python -m venv .venv
  echo    .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)

echo 스크리너 대시보드를 시작합니다... 브라우저에서 http://localhost:8501 로 열립니다.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false

echo.
echo 서버가 종료되었습니다.
pause
