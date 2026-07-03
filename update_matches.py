import requests
import json
import os
from datetime import datetime, timedelta

# Settings
MATCH_FILE = "matches.json"
API_KEY = os.getenv("API_FOOTBALL_KEY") # Set this in GitHub Secrets
API_HOST = "v3.football.api-sports.io"
BASE_URL = "https://v3.football.api-sports.io"

# Mapping API-Football Names to your App Slugs/Ranks
LEAGUE_CONFIG = {
    "UEFA Champions League": {"slug": "uefa.champions", "rank": 2},
    "Premier League": {"slug": "eng.1", "rank": 3},
    "La Liga": {"slug": "esp.1", "rank": 4},
    "Bundesliga": {"slug": "ger.1", "rank": 5},
    "Serie A": {"slug": "ita.1", "rank": 6},
    "Ligue 1": {"slug": "fra.1", "rank": 7},
    "UEFA Europa League": {"slug": "uefa.europa", "rank": 8},
    "Saudi Pro League": {"slug": "ksa.1", "rank": 9},
    "MLS": {"slug": "usa.1", "rank": 10},
    "World Cup": {"slug": "fifa.world", "rank": 1},
}

DEFAULT_SERVERS = [
    {"name": "Server 1", "url": "https://example.com/stream1.m3u8"},
    {"name": "Server 2", "url": "https://example.com/stream2.m3u8"}
]

def fetch_matches(date_str):
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST
    }
    url = f"{BASE_URL}/fixtures?date={date_str}"
    try:
        response = requests.get(url, headers=headers, timeout=20)
        return response.json().get('response', [])
    except Exception as e:
        print(f"Error fetching {date_str}: {e}")
        return []

def update():
    if not API_KEY:
        print("Error: API_FOOTBALL_KEY environment variable not set.")
        return

    print("Updating matches from API-Football...")
    
    # Preserve existing league/server data
    data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        try:
            with open(MATCH_FILE, "r", encoding='utf-8') as f:
                old_data = json.load(f)
                data["leagues"] = old_data.get("leagues", {})
        except: pass

    match_list = []
    # Fetch data for Today and Tomorrow to save API calls
    dates_to_fetch = [
        datetime.utcnow().strftime('%Y-%m-%d'),
        (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')
    ]

    for date_str in dates_to_fetch:
        fixtures = fetch_matches(date_str)
        for item in fixtures:
            fixture = item['fixture']
            league = item['league']
            teams = item['teams']
            goals = item['goals']
            status = fixture['status']

            l_name = league['name']
            config = LEAGUE_CONFIG.get(l_name, {"slug": f"league_{league['id']}", "rank": 999})
            l_slug = config['slug']
            l_rank = config['rank']

            # Add league to metadata if new
            if l_slug not in data['leagues']:
                data['leagues'][l_slug] = {"name": l_name, "servers": DEFAULT_SERVERS}

            # Determine Score
            score_text = ""
            if status['short'] != 'NS': # Not Started
                score_text = f"{goals['home'] or 0} - {goals['away'] or 0}"

            match_list.append({
                "match_no": fixture['id'],
                "league_id": l_slug,
                "league_name": l_name,
                "league_rank": l_rank,
                "team": f"{teams['home']['name']} vs {teams['away']['name']}",
                "date": fixture['date'].split('T')[0],
                "time": fixture['date'].split('T')[1][:5],
                "status": status['short'].lower(),
                "score": score_text,
                "teamA_logo": teams['home']['logo'],
                "teamB_logo": teams['away']['logo'],
                "clock": f"{status['elapsed']}'" if status['elapsed'] else status['long'],
                "goal_scorers": "", # API-Football requires extra calls for scorers (saves API quota)
                "venue": fixture['venue']['name'] or "TBD"
            })

    if match_list:
        # Sort: Live first, then by rank, then time
        match_list.sort(key=lambda x: (x['status'] not in ['1h', '2h', 'ht'], x['league_rank'], x['date'], x['time']))
        data['matches'] = match_list

        with open(MATCH_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully updated {len(match_list)} matches.")

if __name__ == "__main__":
    update()
