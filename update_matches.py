import requests
import json
import os
from datetime import datetime, timedelta

MATCH_FILE = "matches.json"

# Extensive ESPN League ID Mapping
LEAGUE_MAP = {
    '2140': {'name': 'FIFA World Cup', 'rank': 1, 'slug': 'fifa.world'},
    '2310': {'name': 'UEFA Champions League', 'rank': 2, 'slug': 'uefa.champions'},
    '700': {'name': 'Premier League', 'rank': 3, 'slug': 'eng.1'},
    '706': {'name': 'La Liga', 'rank': 4, 'slug': 'esp.1'},
    '705': {'name': 'Bundesliga', 'rank': 5, 'slug': 'ger.1'},
    '708': {'name': 'Serie A', 'rank': 6, 'slug': 'ita.1'},
    '707': {'name': 'Ligue 1', 'rank': 7, 'slug': 'fra.1'},
    '2315': {'name': 'UEFA Europa League', 'rank': 8, 'slug': 'uefa.europa'},
    '19434': {'name': 'Saudi Pro League', 'rank': 9, 'slug': 'ksa.1'},
    '714': {'name': 'MLS', 'rank': 10, 'slug': 'usa.1'},
    '2312': {'name': 'UEFA Euro', 'rank': 11, 'slug': 'uefa.euro'},
    '2313': {'name': 'Copa América', 'rank': 12, 'slug': 'conmebol.america'},
    '2314': {'name': 'UEFA Conference League', 'rank': 13, 'slug': 'uefa.conf'},
    '710': {'name': 'Eredivisie', 'rank': 14, 'slug': 'ned.1'},
    '712': {'name': 'Liga Portugal', 'rank': 15, 'slug': 'por.1'},
    '711': {'name': 'Brasileirão', 'rank': 16, 'slug': 'bra.1'},
    '713': {'name': 'Argentine Primera', 'rank': 17, 'slug': 'arg.1'},
    '19416': {'name': 'AFC Champions League Elite', 'rank': 18, 'slug': 'afc.champions.elite'},
    '766': {'name': 'Turkish Super Lig', 'rank': 19, 'slug': 'tur.1'},
    '715': {'name': 'Liga MX', 'rank': 20, 'slug': 'mex.1'},
    '1812': {'name': 'Indian Super League', 'rank': 21, 'slug': 'ind.1'},
    '2316': {'name': 'UEFA Nations League', 'rank': 22, 'slug': 'uefa.nations'},
    '2319': {'name': 'AFC Asian Cup', 'rank': 23, 'slug': 'afc.asian'},
    '2139': {'name': 'World Cup Qualifiers', 'rank': 24, 'slug': 'fifa.world.q'},
    '2322': {'name': 'FA Cup', 'rank': 25, 'slug': 'eng.fa'},
    '2317': {'name': 'EFL Cup (Carabao)', 'rank': 26, 'slug': 'eng.league_cup'},
    '2325': {'name': 'Copa del Rey', 'rank': 27, 'slug': 'esp.copa_del_rey'},
    '2323': {'name': 'DFB-Pokal', 'rank': 28, 'slug': 'ger.dfb_pokal'},
    '2324': {'name': 'Coppa Italia', 'rank': 29, 'slug': 'ita.coppa_italia'},
    '701': {'name': 'Championship', 'rank': 30, 'slug': 'eng.2'},
    '19438': {'name': 'AFC Champions League Two', 'rank': 31, 'slug': 'afc.champions.2'},
    '709': {'name': 'Scottish Premiership', 'rank': 32, 'slug': 'sco.1'},
    '774': {'name': 'Chinese Super League', 'rank': 33, 'slug': 'chn.1'},
    '782': {'name': 'A-League', 'rank': 34, 'slug': 'aus.1'},
    '779': {'name': 'J1 League', 'rank': 35, 'slug': 'jpn.1'},
    '780': {'name': 'K League 1', 'rank': 36, 'slug': 'kor.1'}
}

# Extensive Keyword Detection covering almost all leagues in LEAGUE_MAP
KEYWORD_RULES = [
    {'keywords': ['WORLD CUP', 'WC 2026', 'FIFA'], 'name': 'FIFA World Cup', 'slug': 'fifa.world', 'rank': 1},
    {'keywords': ['CHAMPIONS LEAGUE', 'UCL'], 'name': 'UEFA Champions League', 'slug': 'uefa.champions', 'rank': 2},
    {'keywords': ['PREMIER LEAGUE', 'EPL'], 'name': 'Premier League', 'slug': 'eng.1', 'rank': 3},
    {'keywords': ['LALIGA', 'LA LIGA'], 'name': 'La Liga', 'slug': 'esp.1', 'rank': 4},
    {'keywords': ['BUNDESLIGA'], 'name': 'Bundesliga', 'slug': 'ger.1', 'rank': 5},
    {'keywords': ['SERIE A'], 'name': 'Serie A', 'slug': 'ita.1', 'rank': 6},
    {'keywords': ['LIGUE 1'], 'name': 'Ligue 1', 'slug': 'fra.1', 'rank': 7},
    {'keywords': ['EUROPA LEAGUE', 'UEL'], 'name': 'UEFA Europa League', 'slug': 'uefa.europa', 'rank': 8},
    {'keywords': ['SAUDI PRO', 'SPL', 'ROSHN'], 'name': 'Saudi Pro League', 'slug': 'ksa.1', 'rank': 9},
    {'keywords': ['MLS', 'MAJOR LEAGUE'], 'name': 'MLS', 'slug': 'usa.1', 'rank': 10},
    {'keywords': ['UEFA EURO', 'EURO 2024'], 'name': 'UEFA Euro', 'slug': 'uefa.euro', 'rank': 11},
    {'keywords': ['COPA AMERICA'], 'name': 'Copa América', 'slug': 'conmebol.america', 'rank': 12},
    {'keywords': ['CONFERENCE LEAGUE', 'UECL'], 'name': 'UEFA Conference League', 'slug': 'uefa.conf', 'rank': 13},
    {'keywords': ['EREDIVISIE'], 'name': 'Eredivisie', 'slug': 'ned.1', 'rank': 14},
    {'keywords': ['PORTUGAL', 'PRIMEIRA LIGA'], 'name': 'Liga Portugal', 'slug': 'por.1', 'rank': 15},
    {'keywords': ['BRASILEIRAO', 'BRAZIL'], 'name': 'Brasileirão', 'slug': 'bra.1', 'rank': 16},
    {'keywords': ['ARGENTINE', 'LIGA PROFESIONAL'], 'name': 'Argentine Primera', 'slug': 'arg.1', 'rank': 17},
    {'keywords': ['AFC CHAMPIONS ELITE', 'ACL ELITE'], 'name': 'AFC Champions League Elite', 'slug': 'afc.champions.elite', 'rank': 18},
    {'keywords': ['TURKISH', 'SUPER LIG'], 'name': 'Turkish Super Lig', 'slug': 'tur.1', 'rank': 19},
    {'keywords': ['LIGA MX'], 'name': 'Liga MX', 'slug': 'mex.1', 'rank': 20},
    {'keywords': ['ISL', 'INDIAN SUPER'], 'name': 'Indian Super League', 'slug': 'ind.1', 'rank': 21},
    {'keywords': ['NATIONS LEAGUE'], 'name': 'UEFA Nations League', 'slug': 'uefa.nations', 'rank': 22},
    {'keywords': ['ASIAN CUP'], 'name': 'AFC Asian Cup', 'slug': 'afc.asian', 'rank': 23},
    {'keywords': ['WC QUALIFIER', 'WORLD CUP QUALIFIER'], 'name': 'World Cup Qualifiers', 'slug': 'fifa.world.q', 'rank': 24},
    {'keywords': ['FA CUP'], 'name': 'FA Cup', 'slug': 'eng.fa', 'rank': 25},
    {'keywords': ['CARABAO', 'EFL CUP'], 'name': 'EFL Cup', 'slug': 'eng.league_cup', 'rank': 26},
    {'keywords': ['COPA DEL REY'], 'name': 'Copa del Rey', 'slug': 'esp.copa_del_rey', 'rank': 27},
    {'keywords': ['DFB-POKAL'], 'name': 'DFB-Pokal', 'slug': 'ger.dfb_pokal', 'rank': 28},
    {'keywords': ['COPPA ITALIA'], 'name': 'Coppa Italia', 'slug': 'ita.coppa_italia', 'rank': 29},
    {'keywords': ['CHAMPIONSHIP'], 'name': 'Championship', 'slug': 'eng.2', 'rank': 30},
    {'keywords': ['AFC CHAMPIONS TWO', 'ACL 2'], 'name': 'AFC Champions League Two', 'slug': 'afc.champions.2', 'rank': 31},
    {'keywords': ['SCOTTISH PREMIER'], 'name': 'Scottish Premiership', 'slug': 'sco.1', 'rank': 32},
    {'keywords': ['CHINESE SUPER', 'CSL'], 'name': 'Chinese Super League', 'slug': 'chn.1', 'rank': 33},
    {'keywords': ['A-LEAGUE'], 'name': 'A-League', 'slug': 'aus.1', 'rank': 34},
    {'keywords': ['J1 LEAGUE'], 'name': 'J1 League', 'slug': 'jpn.1', 'rank': 35},
    {'keywords': ['K LEAGUE'], 'name': 'K League 1', 'slug': 'kor.1', 'rank': 36},
    {'keywords': ['FRIENDLY', 'INTL FRIENDLY'], 'name': 'International Friendlies', 'slug': 'intl.friendly', 'rank': 50}
]

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
    # Fetch data from yesterday to 7 days ahead
    for i in range(-1, 8):
        date_str = (datetime.utcnow() + timedelta(days=i)).strftime('%Y%m%d')
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}"

        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code != 200: continue
            resp_json = resp.json()
            events = resp_json.get('events', [])
            api_leagues = {str(l.get('id')): l for l in resp_json.get('leagues', [])}

            for event in events:
                try:
                    league_obj = event.get('league', {})
                    l_id = str(event.get('leagueId') or league_obj.get('id', 'unknown'))
                    
                    l_display_name = league_obj.get('name') or api_leagues.get(l_id, {}).get('name') or event.get('shortName', 'Other League')
                    l_slug = league_obj.get('slug') or f"league_{l_id}"
                    l_rank = 999

                    # 1. ID Match
                    if l_id in LEAGUE_MAP:
                        l_display_name = LEAGUE_MAP[l_id]['name']
                        l_slug = LEAGUE_MAP[l_id]['slug']
                        l_rank = LEAGUE_MAP[l_id]['rank']
                    
                    # 2. Key-word detection fallback
                    full_info = (event.get('name', '') + " " + l_display_name + " " + event.get('shortName', '')).upper()
                    for rule in KEYWORD_RULES:
                        if any(kw in full_info for kw in rule['keywords']):
                            l_display_name = rule['name']
                            l_slug = rule['slug']
                            l_rank = rule['rank']
                            break

                    if l_slug not in final_data['leagues']:
                        final_data['leagues'][l_slug] = {"name": l_display_name, "servers": DEFAULT_SERVERS}
                    else:
                        final_data['leagues'][l_slug]['name'] = l_display_name

                    comp = event['competitions'][0]
                    status_obj = event['status']
                    status_type = status_obj['type']['state']
                    home = comp['competitors'][0]
                    away = comp['competitors'][1]

                    dt_utc = datetime.strptime(event['date'], '%Y-%m-%dT%H:%MZ')

                    match_list.append({
                        "match_no": int(event['id']),
                        "league_id": l_slug,
                        "league_name": l_display_name,
                        "league_rank": l_rank,
                        "team": f"{home['team'].get('displayName', 'TBD')} vs {away['team'].get('displayName', 'TBD')}",
                        "date": dt_utc.strftime('%Y-%m-%d'),
                        "time": dt_utc.strftime('%H:%M'),
                        "status": status_type,
                        "score": f"{home.get('score', '0')} - {away.get('score', '0')}" if status_type != 'pre' else "",
                        "teamA_logo": home['team'].get('logo', ''),
                        "teamB_logo": away['team'].get('logo', ''),
                        "clock": status_obj['type'].get('detail', ''),
                        "goal_scorers": get_scorers(comp),
                        "venue": comp.get('venue', {}).get('fullName', '')
                    })
                except: continue
        except: continue

    if match_list:
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))
        final_data['matches'] = match_list
        with open(MATCH_FILE, "w", encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
        print(f"Update: {len(match_list)} matches.")

if __name__ == "__main__":
    update()
