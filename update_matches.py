import requests
import json
import os
import base64
from datetime import datetime, timedelta

# Settings
MATCH_FILE = "matches.json"
# API_FOOTBALL_KEY should be set in GitHub Secrets or Environment Variables
API_KEY = os.getenv("API_FOOTBALL_KEY") 
API_HOST = "v3.football.api-sports.io"
BASE_URL = "https://v3.football.api-sports.io"

# GitHub Settings (For API Update)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "realtchat/football-tv-data" 
FILE_PATH = "matches.json"

def push_to_github(data):
    """Updates the JSON file on GitHub using the REST API."""
    if not GITHUB_TOKEN:
        print("Note: GITHUB_TOKEN not set. Remote update via API skipped.")
        return

    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get the current file's SHA (required for updating)
    sha = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json().get('sha')
    except Exception as e:
        print(f"Error fetching SHA: {e}")

    # 2. Encode content to Base64
    json_content = json.dumps(data, indent=4, ensure_ascii=False)
    content_base64 = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')

    # 3. Push the update
    payload = {
        "message": f"Auto-update matches: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": content_base64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    try:
        res = requests.put(url, headers=headers, json=payload)
        if res.status_code in [200, 201]:
            print("Successfully updated matches.json via GitHub API.")
        else:
            print(f"GitHub API Error ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"Failed to push to GitHub: {e}")

# Mapping API-Football League IDs to your App Slugs/Ranks
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
    {"name": "Server 2", "url": "https://hello.1yallashoot.com/splayer/Live1.php"},
    {"name": "Server 2", "url": "https://topx.poiy.online/albaplayer/max1/?serv=8"},
    {"name": "Server 2", "url": "https://topx.poiy.online/albaplayer/max1/?serv=6"}

]

def fetch_fixtures(date_str):
    if not API_KEY:
        print("Error: API_FOOTBALL_KEY environment variable is not set.")
        return []
    
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    url = f"{BASE_URL}/fixtures?date={date_str}"
    try:
        print(f"Calling API for date: {date_str}...")
        response = requests.get(url, headers=headers, timeout=20)
        data = response.json()
        fixtures = data.get('response', [])
        print(f"Found {len(fixtures)} total fixtures in API response for {date_str}.")
        return fixtures
    except Exception as e:
        print(f"Error fetching {date_str}: {e}")
        return []

def update():
    print("Updating matches from API-Football...")
    
    # Load old data to preserve manual server changes
    data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        try:
            with open(MATCH_FILE, "r", encoding='utf-8') as f:
                old_data = json.load(f)
                data["leagues"] = old_data.get("leagues", {})
                print(f"Loaded {len(data['leagues'])} existing leagues from {MATCH_FILE}.")
        except Exception as e:
            print(f"Error loading {MATCH_FILE}: {e}")

    match_list = []
    # Fetch yesterday, today, and the next 30 days
    today = datetime.utcnow()
    dates = [(today + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(-1, 31)]

    for date_str in dates:
        fixtures = fetch_fixtures(date_str)
        for item in fixtures:
            fixture = item['fixture']
            league = item['league']
            teams = item['teams']
            goals = item['goals']
            status = fixture['status']

            l_id = str(league['id'])
            config = LEAGUE_CONFIG.get(l_id, {"slug": f"league_{l_id}", "rank": 999})
            l_slug = config['slug']
            l_rank = config['rank']
            l_name = league['name']

            # Update league metadata
            if l_slug not in data['leagues']:
                data['leagues'][l_slug] = {"name": l_name, "servers": DEFAULT_SERVERS}
            else:
                data['leagues'][l_slug]['name'] = l_name

            # Determine Score
            score_text = ""
            if status['short'] not in ['NS', 'TBD']:
                home_g = goals['home'] if goals['home'] is not None else 0
                away_g = goals['away'] if goals['away'] is not None else 0
                score_text = f"{home_g} - {away_g}"

            # Map API status to App status (in, pre, ft)
            app_status = "pre"
            if status['short'] in ['1H', 'HT', '2H', 'ET', 'BT', 'P']:
                app_status = "in"
            elif status['short'] in ['FT', 'AET', 'PEN']:
                app_status = "ft"

            match_list.append({
                "match_no": fixture['id'],
                "league_id": l_slug,
                "league_name": l_name,
                "league_rank": l_rank,
                "team": f"{teams['home']['name']} vs {teams['away']['name']}",
                "date": fixture['date'].split('T')[0],
                "time": fixture['date'].split('T')[1][:5],
                "status": app_status,
                "score": score_text,
                "teamA_logo": teams['home']['logo'],
                "teamB_logo": teams['away']['logo'],
                "clock": f"{status['elapsed']}'" if status['elapsed'] else status['long'],
                "goal_scorers": "",
                "venue": (fixture['venue']['name'] or "TBD") if 'venue' in fixture else "TBD"
            })

    if match_list:
        # Sort: Live first, then by league rank, then by date/time
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
        data['matches'] = match_list

        with open(MATCH_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully updated {len(match_list)} matches in {MATCH_FILE}.")
        
        # Also push to GitHub API
        push_to_github(data)
    else:
        print("No matches were processed. Check if API Key is correct and has quota.")

if __name__ == "__main__":
    update()
