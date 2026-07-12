# AppRadar — Competitor Intelligence

## Kurulum (1 dakika)

### Windows
```
start.bat çift tıkla → tarayıcı otomatik açılır
```

### Mac / Linux
```bash
chmod +x start.sh
./start.sh
```

### Manuel
```bash
pip install flask requests
python app.py
# → http://localhost:5000
```

---

## API Keyler

**Settings** tab'ından gir, **Kaydet**'e bas.

| Servis | Nereden alınır |
|--------|---------------|
| Groq   | https://console.groq.com → API Keys |
| Apify  | https://console.apify.com → Settings → Integrations |

---

## Kullanım

1. `start.bat` (veya `start.sh`) çalıştır
2. Settings → API keylerini gir → Kaydet
3. Scraper → App ID gir (örn: `com.myfitnesspal.android`)
4. ▶ Start Scraping
5. AI Analysis → sol panelden analiz seç

---

## Apify Aktörleri

Varsayılan aktörler ücretsiz tier ile çalışır (~$5/ay kredi):
- Google Play: `compass/google-play-scraper`
- App Store: `nguyend59/app-store-reviews-scraper`

Alternatif aktörler Settings'ten değiştirilebilir.
