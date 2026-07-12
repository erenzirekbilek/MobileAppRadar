@echo off
echo.
echo  ==========================================
echo   AppRadar - Competitor Intelligence Tool
echo  ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi. python.org'dan yukle.
    pause
    exit /b
)

echo [*] Bagimliliklar kontrol ediliyor...
python -c "import flask" >nul 2>&1 || pip install flask -q
python -c "import requests" >nul 2>&1 || pip install requests -q
python -c "import google_play_scraper" >nul 2>&1 || pip install google-play-scraper -q
python -c "import serpapi" >nul 2>&1 || pip install google-search-results -q
echo [*] Hazir.

echo [*] AppRadar baslatiliyor...
echo [*] http://localhost:5000
echo.
echo  Durdurmak icin: Ctrl+C
echo.

start "" http://localhost:5000
python app.py
pause
