import requests
import json
import os
from datetime import datetime, timedelta

MATCH_FILE = "matches.json"

# লিগ র‍্যাঙ্কিং (অ্যাপে সাজানোর জন্য)
LEAGUE_CONFIG = {
    'international': {'name': 'International Match', 'rank': 1},
    'fifa.world': {'name': 'FIFA World Cup', 'rank': 2},
    'uefa.euro': {'name': 'UEFA Euro', 'rank': 3},
    'uefa.champions': {'name': 'UEFA Champions League', 'rank': 4},
    'eng.1': {'name': 'English Premier League', 'rank': 5},
    'esp.1': {'name': 'La Liga', 'rank': 6},
    'ger.1': {'name': 'Bundesliga', 'rank': 7},
    'ita.1': {'name': 'Serie A', 'rank': 8},
    'fra.1': {'name': 'Ligue 1', 'rank': 9},
    'uefa.europa': {'name': 'UEFA Europa League', 'rank': 10}
}

# ডিফল্ট সার্ভার (যদি লিগের জন্য আগে থেকে কোনো সার্ভার না থাকে)
DEFAULT_SERVERS = [
    {"name": "Server 1", "url": "https://example.com/stream1.m3u8"},
    {"name": "Server 2", "url": "https://example.com/stream2.m3u8"}
]

def get_scorers(competition):
    scorers = []
    details = competition.get('details', [])
    if not isinstance(details, list): return ""
    for detail in details:
        if detail.get('type', {}).get('text') == 'Goal':
            athletes = detail.get('athletesInvolved', [])
            player = athletes[0].get('displayName', 'Unknown') if athletes else 'Unknown'
            clock = detail.get('clock', {}).get('displayValue', '')
            scorers.append(f"{player} ({clock})")
    return ", ".join(scorers)

def update():
    # ১. পুরানো ডাটা লোড করা (সার্ভার লিস্ট ধরে রাখার জন্য)
    data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        try:
            with open(MATCH_FILE, "r", encoding='utf-8') as f:
                old_data = json.load(f)
                if isinstance(old_data, dict):
                    data["leagues"] = old_data.get("leagues", {})
        except:
            print("Could not read old matches.json, starting fresh.")

    # ২. নতুন ম্যাচ ফেচ করা
    match_list = []
    # গতকাল, আজ এবং আগামীকালের ম্যাচ চেক করবে
    for i in range(-1, 2):
        date_str = (datetime.utcnow() + timedelta(days=i)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}"
        
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200: continue
            
            events = resp.json().get('events', [])
            for event in events:
                try:
                    comp = event['competitions'][0]
                    status_obj = event['status']
                    status_type = status_obj['type']['state'] # 'pre', 'in', or 'post'
                    
                    home = comp['competitors'][0]
                    away = comp['competitors'][1]
                    
                    league_obj = event.get('league', {})
                    l_id = league_obj.get('slug', 'soccer')
                    l_name = league_obj.get('name', 'Other League')
                    
                    # যদি এই লিগ আগে থেকে না থাকে, তবে ডিফল্ট সার্ভার দিয়ে এড করো
                    if l_id not in data['leagues']:
                        config = LEAGUE_CONFIG.get(l_id, {'name': l_name, 'rank': 999})
                        data['leagues'][l_id] = {
                            "name": config['name'],
                            "servers": DEFAULT_SERVERS
                        }

                    l_rank = LEAGUE_CONFIG.get(l_id, {'rank': 999})['rank']
                    
                    score = ""
                    if status_type != 'pre':
                        score = f"{home.get('score', '0')} - {away.get('score', '0')}"

                    # টাইম ফরম্যাট করা
                    dt = datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ')

                    match_list.append({
                        "match_no": int(event['id']),
                        "league_id": l_id,
                        "league_name": data['leagues'][l_id]['name'],
                        "league_rank": l_rank,
                        "team": f"{home['team']['displayName']} vs {away['team']['displayName']}",
                        "date": dt.strftime('%Y-%m-%d'),
                        "time": dt.strftime('%H:%M'),
                        "status": status_type,
                        "score": score,
                        "teamA_logo": home['team'].get('logo', ''),
                        "teamB_logo": away['team'].get('logo', ''),
                        "clock": status_obj['type'].get('detail', ''),
                        "goal_scorers": get_scorers(comp),
                        "venue": comp.get('venue', {}).get('fullName', 'TBD')
                    })
                except: continue
        except: continue

    # ৩. যদি কোনো ম্যাচ পাওয়া যায় তবেই সেভ করো
    if match_list:
        # লাইভ ম্যাচগুলো আগে দেখাবে, তারপর র‍্যাঙ্ক অনুযায়ী
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
        data['matches'] = match_list

        with open(MATCH_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully updated {len(match_list)} matches.")
    else:
        print("No matches found from API. File not updated to prevent wiping.")

if __name__ == "__main__":
    update()
