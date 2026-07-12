#!/bin/bash
echo ""
echo " =========================================="
echo "  AppRadar - Competitor Intelligence Tool"
echo " =========================================="
echo ""

# Flask yoksa yükle
pip install flask requests -q

echo " [*] AppRadar başlatılıyor..."
echo " [*] Tarayıcı: http://localhost:5000"
echo ""
echo " Durdurmak için: Ctrl+C"
echo ""

# Tarayıcıyı aç (Mac ve Linux)
sleep 1
if [[ "$OSTYPE" == "darwin"* ]]; then
    open http://localhost:5000
else
    xdg-open http://localhost:5000 2>/dev/null || true
fi

python3 app.py
