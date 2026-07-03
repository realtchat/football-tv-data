import requests
import json
import time
import subprocess
import os
import sys
from datetime import datetime, timedelta, timezone

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

def get_scorers(competition):
    scorers = []
    details = competition.get('details', [])
    if not isinstance(details, list):
        return ""
        
    for detail in details:
        if detail.get('type', {}).get('text') == 'Goal':
            athletes = detail.get('athletesInvolved', [])
            player = athletes[0].get('displayName', 'Unknown') if athletes else 'Unknown'
            clock = detail.get('clock', {}).get('displayValue', '')
            scorers.append(f"{player} ({clock})")
    return ", ".join(scorers)

def update_data():
    try:
        data = {"leagues": {}, "matches": []}

        # Use timezone-aware UTC now
        today = datetime.now(timezone.utc)
        start_date = (today - timedelta(days=1)).strftime('%Y%m%d')
        end_date = (today + timedelta(days=3)).strftime('%Y%m%d')
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={start_date}-{end_date}&limit=500"
        
        match_list = []
        response = requests.get(url, timeout=20)
        response.raise_for_status() # Check for HTTP errors
        
        events = response.json().get('events', [])
        
        for event in events:
            competitions = event.get('competitions', [{}])
            if not competitions: continue
            comp = competitions[0]
            
            status = event.get('status', {})
            status_type = status.get('type', {}).get('state', 'pre')
            
            competitors = comp.get('competitors', [])
            if len(competitors) < 2: continue
            
            home = competitors[0]
            away = competitors[1]
            
            score_str = ""
            if status_type != 'pre':
                home_score = home.get('score', '0')
                away_score = away.get('score', '0')
                score_str = f"{home_score} - {away_score}"

            utc_date = event.get('date', '')
            try:
                dt = datetime.strptime(utc_date, '%Y-%m-%dT%H:%MZ')
            except ValueError:
                dt = today

            league_obj = event.get('league', {})
            raw_league_id = league_obj.get('slug', 'soccer')
            league_display_name = league_obj.get('name', 'Other Leagues')
            
            league_info = LEAGUE_CONFIG.get(raw_league_id)
            if not league_info:
                if "International" in league_display_name or "FIFA" in league_display_name:
                    league_info = LEAGUE_CONFIG['international']
                else:
                    league_info = {'name': league_display_name, 'rank': 999}

            clock_val = status.get('type', {}).get('detail', '')
            if status_type == 'in':
                 clock_val = status.get('displayValue', clock_val)

            scorers_str = get_scorers(comp)

            match_data = {
                "match_no": int(event.get('id', 0)),
                "league_id": raw_league_id,
                "league_name": league_info['name'],
                "league_rank": league_info['rank'],
                "team": f"{home.get('team', {}).get('displayName', 'TBD')} vs {away.get('team', {}).get('displayName', 'TBD')}",
                "date": dt.strftime('%Y-%m-%d'),
                "time": dt.strftime('%H:%M'),
                "status": status_type,
                "score": score_str,
                "teamA_logo": home.get('team', {}).get('logo', ''),
                "teamB_logo": away.get('team', {}).get('logo', ''),
                "clock": clock_val,
                "goal_scorers": scorers_str,
                "venue": comp.get('venue', {}).get('fullName', '')
            }
            match_list.append(match_data)

        # Sort: Live matches first, then by league rank, then by date/time
        match_list.sort(key=lambda x: (x['status'] != 'in', x['league_rank'], x['date'], x['time']))

        data['matches'] = match_list
        with open('matches.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Update successful. Total matches: {len(match_list)}")
        return True

    except Exception as e:
        print(f"Error during update: {e}")
        return False

def push_to_github():
    if os.environ.get('GITHUB_ACTIONS'):
        print("Running in GitHub Actions. Skipping internal git push.")
        return

    try:
        subprocess.run(["git", "add", "matches.json"], check=True)
        commit_msg = f"Auto-update matches: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        print("GitHub update successful.")
    except Exception as e:
        print(f"Local GitHub Push Error: {e}")

if __name__ == "__main__":
    if os.environ.get('GITHUB_ACTIONS'):
        update_data()
        sys.exit(0)
    
    while True:
        if update_data():
            push_to_github()
        
        next_run = (datetime.now() + timedelta(minutes=15)).strftime('%H:%M:%S')
        print(f"Waiting for 15 minutes... (Next update: {next_run})")
        time.sleep(900)
