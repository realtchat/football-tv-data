import requests
import json
from datetime import datetime, timedelta

def update_data():
    # বর্তমান matches.json ফাইলটি পড়া যাতে 'leagues' তথ্য ঠিক থাকে
    try:
        with open('matches.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"leagues": {}, "matches": []}

    existing_matches = data.get('matches', [])
    # ডুপ্লিকেট এড়াতে একটি ইউনিক কি তৈরি করা (TeamNames + Date)
    match_map = {f"{m['team']}_{m['date']}": m for m in existing_matches}

    today = datetime.utcnow()
    
    # গত ২ দিন থেকে আগামী ১৪ দিনের রেঞ্জ (মোট ১৭ দিন)
    for i in range(-2, 15):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime('%Y%m%d')
        
        # ESPN-এর সকল ফুটবলের স্কোরবোর্ড API
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}"
        
        try:
            response = requests.get(url, timeout=15)
            events = response.json().get('events', [])
            
            for event in events:
                comp = event['competitions'][0]
                home_team = comp['competitors'][0]['team']['displayName']
                away_team = comp['competitors'][1]['team']['displayName']
                
                # আপনার JSON ফরম্যাটের সাথে মিল রাখা
                match_id = int(event['id'])
                team_str = f"{home_team} vs {away_team}"
                utc_date = event['date'] # ফরম্যাট: 2024-05-20T18:00Z
                dt = datetime.strptime(utc_date, '%Y-%m-%dT%H:%MZ')
                
                match_date = dt.strftime('%Y-%m-%d')
                match_time = dt.strftime('%H:%M')
                
                unique_key = f"{team_str}_{match_date}"
                
                # যদি ম্যাচটি আগে থেকে না থাকে তবেই যুক্ত হবে
                match_map[unique_key] = {
                    "match_no": match_id,
                    "league_id": event['season']['slug'] if 'season' in event else "soccer",
                    "team": team_str,
                    "date": match_date,
                    "time": match_time,
                    "timezone": "UTC",
                    "teamA_logo": comp['competitors'][0]['team'].get('logo', ''),
                    "teamB_logo": comp['competitors'][1]['team'].get('logo', '')
                }
        except Exception as e:
            print(f"Error fetching date {date_str}: {e}")

    # আজকের তারিখের ২ দিন আগের ম্যাচগুলো মুছে ফেলা
    threshold_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
    final_matches = [m for m in match_map.values() if m['date'] >= threshold_date]
    
    # তারিখ অনুযায়ী সাজানো
    final_matches.sort(key=lambda x: (x['date'], x['time']))

    # আপডেট করা লিস্ট ডেটায় বসানো
    data['matches'] = final_matches

    # ফাইলটি সেভ করা
    with open('matches.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully updated. Total matches: {len(final_matches)}")

if __name__ == "__main__":
    update_data()
