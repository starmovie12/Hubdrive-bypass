from flask import Flask, request, jsonify
import cloudscraper
import re

app = Flask(__name__)

# --- CONFIGURATION ---
# Cloudscraper setup (Mobile Browser Mode)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'desktop': False})

# Jo links CHAHIYE
WANTED_DOMAINS = ["r2.dev", "fsl-lover.buzz", "fsl-cdn-1.sbs", "fukggl.buzz", "cdn.fukggl.buzz"]

# Jo links NAHI CHAHIYE
IGNORE_DOMAINS = ["pixeldrain", "hubcdn", "workers.dev", ".zip"]

def get_real_links(target_url):
    try:
        # Step 1: Main HubCloud Page visit
        resp = scraper.get(target_url)
        if resp.status_code != 200:
            return {"error": "Main page load nahi hua"}
            
        # Regex se hidden 'Generate Link' URL dhundo
        first_match = re.search(r'href="([^"]+hubcloud\.php\?[^"]+)"', resp.text)
        
        if not first_match:
             # Fallback: Agar ID 'download' ho
             first_match = re.search(r'id="download" href="([^"]+)"', resp.text)

        if not first_match:
            return {"error": "Generate Link button nahi mila"}
            
        redirect_url = first_match.group(1).replace('&amp;', '&')
        
        # Step 2: Redirect Page visit (Headers ke sath)
        headers = {"Referer": target_url}
        resp2 = scraper.get(redirect_url, headers=headers)
        
        # --- Step 3: MAGIC SEARCH (Regex) ---
        page_content = resp2.text
        found_links = set()
        
        # Regex to find links ending with token=...
        matches = re.findall(r'(https?://[^"\s\'<>]+token=[a-zA-Z0-9_]+)', page_content)
        for link in matches:
            found_links.add(link)
            
        # Regex 2: Alternate format
        matches2 = re.findall(r'(https?://[^"\s\'<>]+mkv\?[^"\s\'<>]+)', page_content)
        for link in matches2:
            found_links.add(link)

        # Step 4: Filtering
        final_list = []
        for link in found_links:
            # Check Filters
            is_wanted = any(w in link for w in WANTED_DOMAINS)
            is_ignored = any(i in link for i in IGNORE_DOMAINS)
            
            if is_wanted and not is_ignored:
                clean_link = link.strip('"').strip("'")
                final_list.append(clean_link)
        
        final_list.sort()
        
        return {
            "status": "success", 
            "total": len(final_list), 
            "links": final_list
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- API ROUTE ---
@app.route('/get-links', methods=['GET'])
def api_handler():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL missing"}), 400
        
    result = get_real_links(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
