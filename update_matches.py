import requests
import json
import os
import base64
from datetime import datetime, timedelta

# Settings
MATCH_FILE = "matches.json"

# GitHub Settings (For API Update)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "realtchat/football-tv-data" 
FILE_PATH = "matches.json"

# ESPN League Mapping
LEAGUE_CONFIG = {
    "fifa.world": {"name": "FIFA World Cup", "rank": -1},
    "uefa.champions": {"name": "UEFA Champions League", "rank": 0},
    "eng.1": {"name": "Premier League", "rank": 1},
    "esp.1": {"name": "La Liga", "rank": 2},
    "ger.1": {"name": "Bundesliga", "rank": 3},
    "ita.1": {"name": "Serie A", "rank": 4},
    "fra.1": {"name": "Ligue 1", "rank": 5},
    "uefa.europa": {"name": "UEFA Europa League", "rank": 6},
    "ksa.1": {"name": "Saudi Pro League", "rank": 7},
    "uefa.euro": {"name": "UEFA European Championship", "rank": 8},
    "conmebol.america": {"name": "Copa América", "rank": 9},
    "usa.1": {"name": "MLS", "rank": 10},
    "ned.1": {"name": "Eredivisie", "rank": 11},
    "por.1": {"name": "Liga Portugal", "rank": 12},
    "tur.1": {"name": "Turkish Süper Lig", "rank": 13},
    "bra.1": {"name": "Serie A Brazil", "rank": 14},
    "arg.1": {"name": "Argentine Primera", "rank": 15},
    "afc.champions": {"name": "AFC Champions League", "rank": 16},
    "fifa.friendly": {"name": "International Friendlies", "rank": 20},
    "mex.1": {"name": "Liga MX", "rank": 21},
    "eng.2": {"name": "Championship", "rank": 22}
}

DEFAULT_SERVERS = [
    {"name": "Server 1", "url": "https://live05.miekgo.app/live/78905744.m3u8"},
    {"name": "Server 2", "url": "https://live05.miekgo.app/live/14830711.m3u8"},
    {"name": "Server 3", "url": "https://1nyaler.streamhostingcdn.top/stream/23/index.m3u8"},
    {"name": "Server 4", "url": "https://flussonic.deltainfonet.com/01_Tsports_HD/tracks-v1a1/mono.m3u8"}
]

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

    sha = None
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sha = response.json().get('sha')
    except Exception: pass

    json_content = json.dumps(data, indent=4, ensure_ascii=False)
    content_base64 = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')

    payload = {
        "message": f"ESPN Score Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "content": content_base64,
        "branch": "main"
    }
    if sha: payload["sha"] = sha

    try:
        res = requests.put(url, headers=headers, json=payload)
        if res.status_code in [200, 201]:
            print("Successfully updated matches.json via GitHub API.")
        else:
            print(f"GitHub API Error ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"Failed to push to GitHub: {e}")

def fetch_espn_data(league_slug, date_str=None):
    """Fetches data from ESPN's public API for a specific date."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_slug}/scoreboard"
    if date_str:
        url += f"?dates={date_str}"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching ESPN {league_slug} for {date_str}: {e}")
    return None

def update():
    print("Updating matches from ESPN (Extended Schedule)...")
    
    data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        try:
            with open(MATCH_FILE, "r", encoding='utf-8') as f:
                data = json.load(f)
        except Exception: pass

    # We keep all previous matches to avoid re-fetching everything every time
    # But we will filter them by date later.
    existing_matches = {str(m['match_no']): m for m in data.get('matches', [])}
    
    now = datetime.utcnow()
    # To save resources, we fetch a full 30-day window only if it's the first run of the hour
    # Otherwise, we just fetch Today and Tomorrow to update live scores.
    if now.minute < 10:
        print("Syncing 30-day schedule...")
        date_range = 30
    else:
        print("Syncing 2-day window (Live updates)...")
        date_range = 2

    dates_to_fetch = [(now + timedelta(days=i)).strftime('%Y%m%d') for i in range(date_range)]
    
    for date_str in dates_to_fetch:
        print(f"Fetching data for {date_str}...")
        for slug, config in LEAGUE_CONFIG.items():
            espn_json = fetch_espn_data(slug, date_str)
            if not espn_json: continue

            events = espn_json.get('events', [])
            for event in events:
                try:
                    competition = event['competitions'][0]
                    status_type = event['status']['type']['name']
                    short_status = event['status']['type']['shortDetail']
                    
                    home_team = next(t for t in competition['competitors'] if t['homeAway'] == 'home')
                    away_team = next(t for t in competition['competitors'] if t['homeAway'] == 'away')

                    app_status = "pre"
                    if "PROGRESS" in status_type or "HALFTIME" in status_type:
                        app_status = "in"
                    elif "FINAL" in status_type or "FULL_TIME" in status_type:
                        app_status = "ft"

                    raw_date = event['date']
                    dt_obj = datetime.strptime(raw_date, "%Y-%m-%dT%H:%MZ")
                    date_iso = dt_obj.strftime("%Y-%m-%d")
                    time_str = dt_obj.strftime("%H:%M")

                    if slug not in data['leagues']:
                        data['leagues'][slug] = {"name": config['name'], "servers": DEFAULT_SERVERS}

                    match_id = event['id']
                    existing_matches[match_id] = {
                        "match_no": int(match_id),
                        "league_id": slug,
                        "league_name": config['name'],
                        "league_rank": config['rank'],
                        "team": f"{home_team['team']['displayName']} vs {away_team['team']['displayName']}",
                        "date": date_iso,
                        "time": time_str,
                        "status": app_status,
                        "score": f"{home_team['score']} - {away_team['score']}" if app_status != "pre" else "VS",
                        "teamA_logo": home_team['team'].get('logo', ""),
                        "teamB_logo": away_team['team'].get('logo', ""),
                        "clock": short_status if app_status == "in" else ("FT" if app_status == "ft" else ""),
                        "venue": competition.get('venue', {}).get('fullName', "TBD")
                    }
                except Exception: continue

    # AUTO-DELETE LOGIC:
    # 24 hours previous match need delete auto
    yesterday_str = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    
    final_list = [m for m in existing_matches.values() if m['date'] >= yesterday_str]
    
    # Sort: Live first, then Rank, then Date
    final_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
    data['matches'] = final_list

    with open(MATCH_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully updated {len(final_list)} matches (Window: Yesterday to +30 Days).")
    push_to_github(data)

if __name__ == "__main__":
    update()
