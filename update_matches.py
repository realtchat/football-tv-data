import requests
import json
import os
import base64
from datetime import datetime, timedelta

# Settings
MATCH_FILE = "matches.json"
API_KEY = os.getenv("API_FOOTBALL_KEY") 
API_HOST = "v3.football.api-sports.io"
BASE_URL = "https://v3.football.api-sports.io"

# GitHub Settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "realtchat/football-tv-data" 
FILE_PATH = "matches.json"

LEAGUE_CONFIG = {
    "1": {"slug": "fifa.world", "rank": 1},
    "2": {"slug": "uefa.champions", "rank": 2},
    "3": {"slug": "uefa.europa", "rank": 8},
    "39": {"slug": "eng.1", "rank": 3},
    "140": {"slug": "esp.1", "rank": 4},
    "78": {"slug": "ger.1", "rank": 5},
    "135": {"slug": "ita.1", "rank": 6},
    "61": {"slug": "fra.1", "rank": 7},
    "307": {"slug": "ksa.1", "rank": 9},
    "253": {"slug": "usa.1", "rank": 10},
    "4": {"slug": "uefa.euro", "rank": 11},
    "9": {"slug": "conmebol.america", "rank": 12},
    "848": {"slug": "uefa.conf", "rank": 13},
    "88": {"slug": "ned.1", "rank": 14},
    "94": {"slug": "por.1", "rank": 15},
    "71": {"slug": "bra.1", "rank": 16},
    "103": {"slug": "arg.1", "rank": 17},
    "40": {"slug": "eng.2", "rank": 30},
    "235": {"slug": "afc.champions", "rank": 18},
    "203": {"slug": "tur.1", "rank": 19},
    "262": {"slug": "mex.1", "rank": 20},
    "323": {"slug": "ind.1", "rank": 21},
}

DEFAULT_SERVERS = [
    {"name": "Server 1", "url": "https://hello.1yallashoot.com/splayer/Live6.php"},
    {"name": "Server 2", "url": "https://hello.1yallashoot.com/splayer/Live1.php"}
]

def push_to_github(data):
    if not GITHUB_TOKEN: return
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    sha = None
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200: sha = res.json().get('sha')
    except: pass
    
    content_base64 = base64.b64encode(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    payload = {"message": f"Score Update: {datetime.now().strftime('%H:%M')}", "content": content_base64, "branch": "main"}
    if sha: payload["sha"] = sha
    requests.put(url, headers=headers, json=payload)

def fetch_data(date_str):
    headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': API_HOST}
    url = f"{BASE_URL}/fixtures?date={date_str}"
    try:
        response = requests.get(url, headers=headers, timeout=20)
        return response.json().get('response', [])
    except: return []

def update():
    if not API_KEY: return
    
    # To save API quota: 
    # - If it's the top of the hour, fetch next 7 days.
    # - Otherwise, only fetch today's matches for live scores.
    now = datetime.utcnow()
    if now.minute < 10:
        dates = [(now + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(-1, 8)]
    else:
        dates = [now.strftime('%Y-%m-%d')]

    match_list = []
    # Load existing to preserve data we aren't fetching right now
    data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        with open(MATCH_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)

    new_matches = {}
    for date_str in dates:
        fixtures = fetch_data(date_str)
        for item in fixtures:
            f = item['fixture']
            l = item['league']
            t = item['teams']
            g = item['goals']
            s = f['status']

            l_id = str(l['id'])
            config = LEAGUE_CONFIG.get(l_id, {"slug": f"league_{l_id}", "rank": 999})
            
            # Map Score/Status
            score = f"{g['home']} - {g['away']}" if g['home'] is not None else ""
            app_status = "in" if s['short'] in ['1H', 'HT', '2H', 'ET', 'BT', 'P'] else ("ft" if s['short'] in ['FT', 'AET', 'PEN'] else "pre")

            m_data = {
                "match_no": f['id'],
                "league_id": config['slug'],
                "league_name": l['name'],
                "league_rank": config['rank'],
                "team": f"{t['home']['name']} vs {t['away']['name']}",
                "date": f['date'].split('T')[0],
                "time": f['date'].split('T')[1][:5],
                "status": app_status,
                "score": score,
                "teamA_logo": t['home']['logo'],
                "teamB_logo": t['away']['logo'],
                "clock": f"{s['elapsed']}'" if s['elapsed'] else s['long']
            }
            new_matches[f['id']] = m_data
            if config['slug'] not in data['leagues']:
                data['leagues'][config['slug']] = {"name": l['name'], "servers": DEFAULT_SERVERS}

    # Merge new matches into old list
    existing_matches = {m['match_no']: m for m in data.get('matches', [])}
    existing_matches.update(new_matches)
    
    final_list = list(existing_matches.values())
    final_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
    data['matches'] = final_list

    with open(MATCH_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    push_to_github(data)

if __name__ == "__main__":
    update()
