import requests
import json
import os
from datetime import datetime, timedelta

MATCH_FILE = "matches.json"

# প্রধান লিগগুলোর জন্য সুন্দর নাম এবং র‍্যাঙ্কিং
LEAGUE_MAP = {
    'eng.1': {'name': 'English Premier League', 'rank': 1},
    'esp.1': {'name': 'Spanish LALIGA', 'rank': 2},
    'ger.1': {'name': 'German Bundesliga', 'rank': 3},
    'ita.1': {'name': 'Italian Serie A', 'rank': 4},
    'fra.1': {'name': 'French Ligue 1', 'rank': 5},
    'uefa.champions': {'name': 'UEFA Champions League', 'rank': 6},
    'uefa.europa': {'name': 'UEFA Europa League', 'rank': 7},
    'usa.1': {'name': 'Major League Soccer', 'rank': 8},
    'ksa.1': {'name': 'Saudi Pro League', 'rank': 9},
    'fifa.world': {'name': 'FIFA World Cup', 'rank': 10}
}

DEFAULT_SERVERS = [
    {"name": "Server 1", "url": "https://1.simoplay.com/my-hls/0wo68p0w54v.m3u8"},
    {"name": "Server 2", "url": "https://hello.1yallashoot.com/splayer/Live1.php"}
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
    # ১. বিদ্যমান ডাটা লোড করা (সার্ভার ইউআরএল রক্ষা করার জন্য)
    final_data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        try:
            with open(MATCH_FILE, "r", encoding='utf-8') as f:
                old_data = json.load(f)
                if isinstance(old_data, dict):
                    final_data["leagues"] = old_data.get("leagues", {})
        except: pass

    match_list = []
    # ২. গত ২ দিন থেকে আগামী ৩ দিনের ম্যাচ ফেচ করবে
    for i in range(-1, 3):
        date_str = (datetime.utcnow() + timedelta(days=i)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}"
        
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200: continue
            
            resp_json = resp.json()
            events = resp_json.get('events', [])
            
            # মেটাডাটা থেকে লিগের নাম বের করা (এটিই সবচেয়ে সঠিক নাম দেয়)
            meta_leagues = {l.get('slug'): l.get('name') for l in resp_json.get('leagues', [])}
            
            for event in events:
                try:
                    comp = event['competitions'][0]
                    league_obj = event.get('league', {})
                    l_slug = league_obj.get('slug', 'soccer')
                    
                    # নাম নির্ধারণের প্রাওয়োরিটি: ১. আমাদের ম্যাপ, ২. মেটাডাটা, ৩. ইভেন্ট নেম
                    l_display_name = LEAGUE_MAP.get(l_slug, {}).get('name') or meta_leagues.get(l_slug) or league_obj.get('name', 'Other League')
                    
                    # "Spanish LALIGA" এর মতো বড় নামগুলোকে সুন্দর করা
                    if "LALIGA" in l_display_name.upper(): l_display_name = "La Liga"
                    
                    # লিগটি final_data তে না থাকলে এড করা
                    if l_slug not in final_data['leagues']:
                        final_data['leagues'][l_slug] = {
                            "name": l_display_name,
                            "servers": DEFAULT_SERVERS
                        }
                    else:
                        # নাম আপডেট করা (যদি আগে থেকে সার্ভার সেট করা থাকে তবুও)
                        final_data['leagues'][l_slug]['name'] = l_display_name

                    l_rank = LEAGUE_MAP.get(l_slug, {'rank': 999})['rank']
                    status_obj = event['status']
                    status_type = status_obj['type']['state']
                    
                    home = comp['competitors'][0]
                    away = comp['competitors'][1]
                    
                    score = ""
                    if status_type != 'pre':
                        score = f"{home.get('score', '0')} - {away.get('score', '0')}"

                    dt = datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ')

                    match_list.append({
                        "match_no": int(event['id']),
                        "league_id": l_slug,
                        "league_name": l_display_name,
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

    # ৩. ডাটা সেভ করা
    if match_list:
        # সর্টিং: লাইভগুলো উপরে, তারপর র‍্যাঙ্ক অনুযায়ী
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
        final_data['matches'] = match_list

        with open(MATCH_FILE, "w", encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print(f"Update successful: {len(match_list)} matches found.")
    else:
        print("API returned no matches. File preserved.")

if __name__ == "__main__":
    update()
