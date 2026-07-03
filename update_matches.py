import requests
import json
import os
from datetime import datetime, timedelta

MATCH_FILE = "matches.json"

# প্রধান লিগগুলোর ডাটাবেস (র‍্যাঙ্কিং এবং কাস্টম নামের জন্য)
LEAGUE_MAP = {
    # ইউরোপীয় শীর্ষ লিগ
    '700': {'name': 'Premier League', 'rank': 1, 'slug': 'eng.1'},
    '706': {'name': 'La Liga', 'rank': 2, 'slug': 'esp.1'},
    '705': {'name': 'Bundesliga', 'rank': 3, 'slug': 'ger.1'},
    '708': {'name': 'Serie A', 'rank': 4, 'slug': 'ita.1'},
    '707': {'name': 'Ligue 1', 'rank': 5, 'slug': 'fra.1'},
    '710': {'name': 'Eredivisie', 'rank': 12, 'slug': 'ned.1'},
    '712': {'name': 'Liga Portugal', 'rank': 13, 'slug': 'por.1'},
    '709': {'name': 'Scottish Premiership', 'rank': 15, 'slug': 'sco.1'},
    '701': {'name': 'Championship', 'rank': 20, 'slug': 'eng.2'},
    '702': {'name': 'League One', 'rank': 21, 'slug': 'eng.3'},
    '766': {'name': 'Turkish Super Lig', 'rank': 22, 'slug': 'tur.1'},

    # ক্লাব কম্পিটিশন
    '2310': {'name': 'UEFA Champions League', 'rank': 6, 'slug': 'uefa.champions'},
    '2315': {'name': 'UEFA Europa League', 'rank': 7, 'slug': 'uefa.europa'},
    '2314': {'name': 'UEFA Conference League', 'rank': 11, 'slug': 'uefa.conf'},
    '2316': {'name': 'UEFA Nations League', 'rank': 18, 'slug': 'uefa.nations'},
    '19416': {'name': 'AFC Champions League', 'rank': 22, 'slug': 'afc.champions'},

    # আন্তর্জাতিক
    '2140': {'name': 'FIFA World Cup', 'rank': 10, 'slug': 'fifa.world'},
    '2312': {'name': 'UEFA Euro', 'rank': 11, 'slug': 'uefa.euro'},
    '2313': {'name': 'Copa América', 'rank': 14, 'slug': 'conmebol.america'},
    '2319': {'name': 'AFC Asian Cup', 'rank': 16, 'slug': 'afc.asian'},
    '2139': {'name': 'World Cup Qualifiers', 'rank': 25, 'slug': 'fifa.world.q'},

    # আমেরিকা ও এশিয়া
    '714': {'name': 'MLS', 'rank': 8, 'slug': 'usa.1'},
    '19434': {'name': 'Saudi Pro League', 'rank': 9, 'slug': 'ksa.1'},
    '715': {'name': 'Liga MX', 'rank': 17, 'slug': 'mex.1'},
    '711': {'name': 'Brasileirão', 'rank': 18, 'slug': 'bra.1'},
    '713': {'name': 'Argentine Primera', 'rank': 19, 'slug': 'arg.1'},
    '1812': {'name': 'Indian Super League', 'rank': 21, 'slug': 'ind.1'},
    '782': {'name': 'A-League', 'rank': 23, 'slug': 'aus.1'},
    '774': {'name': 'Chinese Super League', 'rank': 24, 'slug': 'chn.1'}
}

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
    final_data = {"leagues": {}, "matches": []}
    if os.path.exists(MATCH_FILE):
        try:
            with open(MATCH_FILE, "r", encoding='utf-8') as f:
                old_data = json.load(f)
                if isinstance(old_data, dict):
                    final_data["leagues"] = old_data.get("leagues", {})
        except: pass

    match_list = []
    for i in range(-1, 5):
        date_str = (datetime.utcnow() + timedelta(days=i)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}"

        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200: continue

            resp_json = resp.json()
            events = resp_json.get('events', [])
            
            # মেটাডাটা থেকে লিগের নাম ও স্ল্যাগ ম্যাপ করা (Dynamic Detection)
            api_leagues = {str(l.get('id')): l for l in resp_json.get('leagues', [])}

            for event in events:
                try:
                    l_id = str(event.get('leagueId'))
                    api_league_info = api_leagues.get(l_id, {})

                    # নাম নির্ধারণের লজিক
                    if l_id in LEAGUE_MAP:
                        l_display_name = LEAGUE_MAP[l_id]['name']
                        l_slug = LEAGUE_MAP[l_id]['slug']
                        l_rank = LEAGUE_MAP[l_id]['rank']
                    else:
                        # যদি এপিআই-তে থাকে কিন্তু আমাদের লিস্টে নেই
                        l_display_name = api_league_info.get('name') or event.get('league', {}).get('name', 'Other League')
                        l_slug = api_league_info.get('slug') or f"league_{l_id}"
                        l_rank = 999

                    # নাম পরিষ্কার করা
                    if "LALIGA" in l_display_name.upper(): l_display_name = "La Liga"

                    if l_slug not in final_data['leagues']:
                        final_data['leagues'][l_slug] = {
                            "name": l_display_name,
                            "servers": DEFAULT_SERVERS
                        }
                    else:
                        # প্রতিবার নাম সিঙ্ক করা
                        final_data['leagues'][l_slug]['name'] = l_display_name

                    comp = event['competitions'][0]
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
                        "team": f"{home['team'].get('displayName', 'TBD')} vs {away['team'].get('displayName', 'TBD')}",
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

    if match_list:
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
        final_data['matches'] = match_list
        with open(MATCH_FILE, "w", encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully updated {len(match_list)} matches.")
    else:
        print("No matches found.")

if __name__ == "__main__":
    update()
