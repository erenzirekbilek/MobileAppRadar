"""
AppRadar - Flask Backend
Scraper: google-play-scraper (ücretsiz) veya SerpApi
AI: Groq proxy
"""

from flask import Flask, request, jsonify, send_from_directory
import requests
import json
import os

app = Flask(__name__, static_folder='.')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
    # Environment variables override config.json (Railway'de config.json kalıcı değil)
    env_map = {
        'GROQ_KEY': 'groqKey',
        'APIFY_KEY': 'apifyKey',
        'SERPAPI_KEY': 'serpapiKey',
        'GROQ_MODEL': 'groqModel',
        'GP_ACTOR': 'gpActor',
        'AS_ACTOR': 'asActor',
        'SCRAPE_ENGINE': 'scrapeEngine',
    }
    for env_key, cfg_key in env_map.items():
        val = os.environ.get(env_key)
        if val:
            cfg[cfg_key] = val
    return cfg

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ─── ROUTES ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    cfg = load_config()
    return jsonify({
        'groqKeySet': bool(cfg.get('groqKey')),
        'apifyKeySet': bool(cfg.get('apifyKey')),
        'serpapiKeySet': bool(cfg.get('serpapiKey')),
        'scrapeEngine': cfg.get('scrapeEngine', 'free'),
        'groqModel': cfg.get('groqModel', 'llama-3.3-70b-versatile'),
        'myAppName': cfg.get('myAppName', ''),
        'myAppCategory': cfg.get('myAppCategory', ''),
        'myAppFeatures': cfg.get('myAppFeatures', ''),
        'myAppPrice': cfg.get('myAppPrice', ''),
        'myAppTarget': cfg.get('myAppTarget', ''),
        'myAppWeakness': cfg.get('myAppWeakness', ''),
        'myAppMdContent': cfg.get('myAppMdContent', ''),
    })

@app.route('/api/config', methods=['POST'])
def set_config():
    cfg = load_config()
    cfg.update(request.json)
    save_config(cfg)
    return jsonify({'ok': True})

@app.route('/api/status', methods=['GET'])
def status():
    cfg = load_config()
    return jsonify({
        'groq': bool(cfg.get('groqKey')),
        'apify': bool(cfg.get('apifyKey')),
        'serpapi': bool(cfg.get('serpapiKey')),
        'engine': cfg.get('scrapeEngine', 'free'),
        'model': cfg.get('groqModel', 'llama-3.3-70b-versatile')
    })

@app.route('/api/scrape', methods=['POST'])
def scrape():
    cfg = load_config()
    body = request.json
    app_id = body.get('appId', '').strip()
    max_reviews = int(body.get('maxReviews', 50))
    country = body.get('country', 'us')
    sort_by = body.get('sortBy', 'NEWEST')
    platform = body.get('platform', 'google_play')
    engine = cfg.get('scrapeEngine', 'free')

    if not app_id:
        return jsonify({'error': 'App ID gerekli'}), 400

    # App Store → her zaman Apify
    if platform == 'app_store':
        return scrape_apify(cfg, app_id, max_reviews, country, sort_by, platform)

    # Google Play → engine seçimi
    if engine == 'serpapi':
        serpapi_key = cfg.get('serpapiKey', '')
        if not serpapi_key:
            return jsonify({'error': 'SerpApi key ayarlanmamış'}), 400
        return scrape_serpapi(serpapi_key, app_id, max_reviews, country, sort_by)
    elif engine == 'apify':
        return scrape_apify(cfg, app_id, max_reviews, country, sort_by, platform)
    else:
        return scrape_free(app_id, max_reviews, country, sort_by)

# ─── FREE SCRAPER ─────────────────────────────────────────────────────────────
def scrape_free(app_id, max_reviews, country, sort_by):
    try:
        from google_play_scraper import reviews, Sort
        sort = Sort.NEWEST if sort_by == 'NEWEST' else Sort.MOST_RELEVANT
        result, _ = reviews(
            app_id,
            lang=country,
            country=country,
            sort=sort,
            count=max_reviews
        )
        # Normalize
        normalized = [{
            'body': r.get('content', ''),
            'rating': r.get('score', 3),
            'date': r.get('at', '').isoformat() if hasattr(r.get('at', ''), 'isoformat') else str(r.get('at', '')),
            'reviewer': r.get('userName', 'User'),
        } for r in result]
        return jsonify(normalized)
    except Exception as e:
        return jsonify({'error': f'Free scraper hatası: {str(e)}'}), 500

# ─── SERPAPI SCRAPER ──────────────────────────────────────────────────────────
def scrape_serpapi(api_key, app_id, max_reviews, country, sort_by):
    try:
        import serpapi
        client = serpapi.Client(api_key=api_key)

        all_reviews = []
        next_page_token = None
        num_per_page = min(199, max_reviews)

        while len(all_reviews) < max_reviews:
            params = {
                'engine': 'google_play_product',
                'product_id': app_id,
                'store': 'apps',
                'all_reviews': 'true',
                'num': num_per_page,
                'gl': country,
            }
            if next_page_token:
                params['next_page_token'] = next_page_token

            results = client.search(params)
            batch = results.get('reviews', [])
            if not batch:
                break

            all_reviews.extend(batch)

            if 'serpapi_pagination' in results and len(all_reviews) < max_reviews:
                next_page_token = results['serpapi_pagination'].get('next_page_token')
                if not next_page_token:
                    break
            else:
                break

        # Normalize
        normalized = [{
            'body': r.get('snippet', ''),
            'rating': r.get('rating', 3),
            'date': r.get('date', ''),
            'reviewer': r.get('username', 'User'),
        } for r in all_reviews[:max_reviews]]

        return jsonify(normalized)
    except Exception as e:
        return jsonify({'error': f'SerpApi hatası: {str(e)}'}), 500

# ─── APIFY SCRAPER ────────────────────────────────────────────────────────────
def scrape_apify(cfg, app_id, max_reviews, country, sort_by, platform):
    apify_token = cfg.get('apifyKey', '')
    if not apify_token:
        return jsonify({'error': 'Apify token ayarlanmamış'}), 400

    if platform == 'google_play':
        actor = cfg.get('gpActor', 'neatrat/google-play-store-reviews-scraper')
        sort_mapped = 'recent' if sort_by == 'NEWEST' else 'top'
        run_input = {
            'appIdOrUrl': app_id,
            'maxReviews': max_reviews,
            'sortBy': sort_mapped,
            'reviewsPerPage': 100,
            'uniqueOnly': True
        }
    else:
        actor = cfg.get('asActor', 'nguyend59/app-store-reviews-scraper')
        run_input = {'id': app_id, 'country': country, 'maxReviews': max_reviews}

    actor_encoded = actor.replace('/', '~')
    url = f'https://api.apify.com/v2/acts/{actor_encoded}/run-sync-get-dataset-items?token={apify_token}&timeout=120'

    try:
        res = requests.post(url, json=run_input, timeout=130)
        if not res.ok:
            return jsonify({'error': f'Apify error {res.status_code}: {res.text[:300]}'}), 502
        return jsonify(res.json())
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Apify timeout. Daha az review dene.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─── GROQ PROXY ──────────────────────────────────────────────────────────────
@app.route('/api/groq', methods=['POST'])
def groq_proxy():
    cfg = load_config()
    groq_key = cfg.get('groqKey', '')
    if not groq_key:
        return jsonify({'error': 'Groq API key ayarlanmamış'}), 400

    try:
        res = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {groq_key}'},
            json=request.json,
            timeout=60
        )
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print('\n' + '='*50)
    print('  AppRadar başlatılıyor...')
    print(f'  http://localhost:{port}')
    print('='*50 + '\n')
    app.run(debug=False, port=port, host='0.0.0.0')
