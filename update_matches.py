import requests
import json
from datetime import datetime, timedelta

def update_data():
    try:
        with open('matches.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"leagues": {}, "matches": []}

    today = datetime.utcnow()
    # ২ দিন আগে থেকে ১৪ দিন পরের রেঞ্জ
    start_date = (today - timedelta(days=2)).strftime('%Y%m%d')
    end_date = (today + timedelta(days=14)).strftime('%Y%m%d')
    
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={start_date}-{end_date}&limit=1000"
    
    match_list = []
    
    try:
        response = requests.get(url, timeout=15)
        events = response.json().get('events', [])
        
        for event in events:
            comp = event['competitions'][0]
            status_type = event['status']['type']['state'] # 'pre', 'in', 'post'
            
            home = comp['competitors'][0]
            away = comp['competitors'][1]
            
            # স্কোর ফরম্যাট করা
            score_str = ""
            if status_type != 'pre': # লাইভ বা শেষ হওয়া ম্যাচের জন্য
                score_str = f"{home['score']} - {away['score']}"

            utc_date = event['date']
            dt = datetime.strptime(utc_date, '%Y-%m-%dT%H:%MZ')
            
            match_data = {
                "match_no": int(event['id']),
                "league_id": event['season']['slug'] if 'season' in event else "soccer",
                "team": f"{home['team']['displayName']} vs {away['team']['displayName']}",
                "date": dt.strftime('%Y-%m-%d'),
                "time": dt.strftime('%H:%M'),
                "status": status_type, # 'in' মানে লাইভ
                "score": score_str,
                "teamA_logo": home['team'].get('logo', ''),
                "teamB_logo": away['team'].get('logo', '')
            }
            match_list.append(match_data)

        # সর্টিং লজিক: 
        # ১. লাইভ ম্যাচ (status == 'in') সবার আগে
        # ২. তারপর তারিখ অনুযায়ী
        match_list.sort(key=lambda x: (x['status'] != 'in', x['date'], x['time']))

        data['matches'] = match_list
        with open('matches.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Update successful. Live: {len([m for m in match_list if m['status']=='in'])}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_data()
