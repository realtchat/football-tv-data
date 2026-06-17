import os
import json
import requests
from datetime import datetime, timedelta

# Settings
MATCH_FILE = "matches.json"
API_KEY = os.getenv("GEMINI_API_KEY")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

def get_live_score(match_name):
    prompt = f"Return only the live football score for '{match_name}' in the format 'TeamA X-Y TeamB'. If the match hasn't started or score is unavailable, return 'No score'."
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(URL, json=payload, timeout=10)
        if response.status_status == 200:
            text = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            return text if "no score" not in text.lower() else None
    except:
        return None

# Load matches
with open(MATCH_FILE, "r") as f:
    data = json.load(f)

# Update scores for live matches
now = datetime.utcnow()
updated = False

for match in data.get("matches", []):
    # Parse UTC time from matches.json
    match_time = datetime.strptime(f"{match['date']} {match['time']}", "%Y-%m-%d %H:%M")
    
    # Check if match is in the 2-hour "Live" window
    if match_time <= now <= (match_time + timedelta(hours=2)):
        new_score = get_live_score(match['team'])
        if new_score:
            match['score'] = new_score
            updated = True

# Save back to file if changed
if updated:
    with open(MATCH_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print("Scores updated successfully.")
else:
    print("No updates needed.")
