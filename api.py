from flask import Flask, request, jsonify
import cloudscraper
import re
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Scraper setup: Android Chrome ban kar request bhejega
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'desktop': False})

# --- HUBDRIVE SOLVER LOGIC ---
def extract_hubcloud(url):
    try:
        # Request bhejo (Timeout thoda badhaya hai taaki slow net pe fail na ho)
        response = scraper.get(url, timeout=15)
        
        # Status code check (Debugging ke liye)
        if response.status_code != 200:
            print(f"❌ Failed to fetch page: {response.status_code}")
            return None

        # Regex Update: Ab ye hubcloud.foo, .club, .space sab pakad lega
        # Pattern: href="https://hubcloud.[kuchbhi]/drive/..."
        pattern = r'href=["\'](https?://hubcloud\.[a-zA-Z0-9-]+\/drive/[^"\']+)["\']'
        
        match = re.search(pattern, response.text)
        
        if match:
            return match.group(1)
        else:
            # Fallback: Agar href me nahi mila, to shayad 'window.location' me ho
            pattern_js = r'window\.location\.replace\(["\'](https?://hubcloud\.[^"\']+)["\']\)'
            match_js = re.search(pattern_js, response.text)
            if match_js:
                return match_js.group(1)
                
        return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# --- HOME PAGE ---
@app.route('/')
def home():
    return "HubDrive Solver API is Running! 🚀 Use /solve?url=YOUR_LINK"

# --- API ENDPOINT ---
@app.route('/solve', methods=['GET'])
def solve():
    target_url = request.args.get('url')
    
    if not target_url:
        return jsonify({"status": "error", "message": "URL missing"}), 400

    extracted = extract_hubcloud(target_url)

    if extracted:
        return jsonify({
            "status": "success",
            "original_url": target_url,
            "hubcloud_link": extracted
        })
    else:
        return jsonify({
            "status": "fail",
            "message": "Link nahi mila (Shayad Cloudflare protection hai ya link expire ho gaya)"
        })

if __name__ == '__main__':
    # Web Server (Render) ke liye Port environment variable se lena zaroori hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
