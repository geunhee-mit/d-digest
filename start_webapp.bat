@echo off
chcp 65001 > nul
echo ========================================================
echo  🍵 고요한 연구 살롱 (Research Digest Salon) 실행 중...
echo ========================================================
echo.
cd /d "%~dp0\web"
echo 브라우저에서 웹앱을 엽니다 (http://localhost:8080)...
start http://localhost:8080
echo.
echo 웹 서버가 실행 중입니다. 종료하려면 이 창에서 Ctrl+C를 누르세요.
python -m http.server 8080
