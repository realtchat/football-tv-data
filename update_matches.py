import requests
import json
from datetime import datetime, timedelta

# League Ranking and Names
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
    'uefa.europa': {'name': 'UEFA Europa League', 'rank': 10},
    'por.1': {'name': 'Primeira Liga', 'rank': 11},
    'ned.1': {'name': 'Eredivisie', 'rank': 12},
    'bra.1': {'name': 'Brasileirão', 'rank': 13},
    'arg.1': {'name': 'Liga Profesional', 'rank': 14},
    'usa.1': {'name': 'MLS', 'rank': 15},
    'ksa.1': {'name': 'Saudi Pro League', 'rank': 16}
}

def update_data():
    try:
        with open('matches.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"leagues": {}, "matches": []}

    today = datetime.utcnow()
    start_date = (today - timedelta(days=2)).strftime('%Y%m%d')
    end_date = (today + timedelta(days=14)).strftime('%Y%m%d')
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={start_date}-{end_date}&limit=1000"
    
    match_list = []
    
    try:
        response = requests.get(url, timeout=15)
        events = response.json().get('events', [])
        
        for event in events:
            comp = event['competitions'][0]
            status_type = event['status']['type']['state']
            
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            
            score_str = ""
            if status_type != 'pre':
                score_str = f"{home['score']} - {away['score']}"

            utc_date = event['date']
            dt = datetime.strptime(utc_date, '%Y-%m-%dT%H:%MZ')
            
            # League Info from Config
            raw_league_id = event['season']['slug'] if 'season' in event else "soccer"
            # ESPN ids can be more complex, trying to find a match in our config
            league_info = LEAGUE_CONFIG.get(raw_league_id, {'name': 'Other Leagues', 'rank': 999})
            
            # Special check for "International" in the display name if not found
            league_display_name = event.get('league', {}).get('name', 'Soccer')
            if "International" in league_display_name or "FIFA" in league_display_name:
                league_info = LEAGUE_CONFIG['international']

            match_data = {
                "match_no": int(event['id']),
                "league_id": raw_league_id,
                "league_name": league_info['name'],
                "league_rank": league_info['rank'],
                "team": f"{home['team']['displayName']} vs {away['team']['displayName']}",
                "date": dt.strftime('%Y-%m-%d'),
                "time": dt.strftime('%H:%M'),
                "status": status_type,
                "score": score_str,
                "teamA_logo": home['team'].get('logo', ''),
                "teamB_logo": away['team'].get('logo', '')
            }
            match_list.append(match_data)

        # Sorting: 
        # 1. Status (Live 'in' first)
        # 2. League Rank (Lower rank number = higher priority)
        # 3. Date & Time
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))

        data['matches'] = match_list
        with open('matches.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Update successful. Total: {len(match_list)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_data()
