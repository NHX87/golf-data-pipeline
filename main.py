import requests
import os
from datetime import datetime

# Load environment variables from GitHub secrets
API_KEY = os.environ["SPORTSDATA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Set headers
headers = {
    "Ocp-Apim-Subscription-Key": API_KEY
}
supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-conflict,return=minimal"
}

# 1. Fetch Players
print("\ud83d\udce1 Fetching players from SportsData.io...")
player_url = "https://api.sportsdata.io/golf/v2/json/Players"
response = requests.get(player_url, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch players: {response.status_code} - {response.text}")
    exit(1)

players = response.json()
print(f"✅ Retrieved {len(players)} players.")

# 2. Insert Players
inserted_players = 0
for p in players:
    data = {
        "player_id": p["PlayerID"],
        "full_name": f"{p['FirstName']} {p['LastName']}",
        "country": p.get("Country"),
        "status": "Active"
    }
    res = requests.post(f"{SUPABASE_URL}/players", headers=supabase_headers, json=data)
    if res.status_code in [201, 204]:
        inserted_players += 1
print(f"🎉 Finished inserting {inserted_players} new players.")

# 3. Fetch Tournaments (2023, 2024, 2025)
print("\ud83d\udce1 Fetching tournaments...")
tournament_urls = [
    "https://api.sportsdata.io/golf/v2/json/Tournaments/2023",
    "https://api.sportsdata.io/golf/v2/json/Tournaments/2024",
    "https://api.sportsdata.io/golf/v2/json/Tournaments/2025"
]

tournaments = []
for url in tournament_urls:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tournaments += response.json()
    else:
        print(f"⚠️ Failed to fetch tournaments: {response.status_code}")

print(f"✅ Retrieved {len(tournaments)} tournaments combined.")

# 4. Filter Completed and In-Progress Tournaments
print("\ud83d\udcc5 Filtering tournaments...")
today = datetime.utcnow().date()
filtered_tournaments = []

for t in tournaments:
    start_date = datetime.fromisoformat(t["StartDate"]).date() if t.get("StartDate") else None
    end_date = datetime.fromisoformat(t["EndDate"]).date() if t.get("EndDate") else None

    if end_date and end_date < today:
        status = "completed"
    elif start_date and start_date <= today <= (end_date or today):
        status = "in_progress"
    else:
        continue  # skip future tournaments

    t["_status"] = status
    filtered_tournaments.append(t)

print(f"📅 {len(filtered_tournaments)} completed or in-progress tournaments.")

# 5. Insert Tournaments
inserted_tournaments = 0
for t in filtered_tournaments:
    data = {
        "tournament_id": t["TournamentID"],
        "name": t["Name"],
        "tour": t.get("Tour"),
        "start_date": t.get("StartDate"),
        "end_date": t.get("EndDate"),
        "location": t.get("Location"),
        "status": t["_status"]
    }
    res = requests.post(f"{SUPABASE_URL}/tournaments", headers=supabase_headers, json=data)
    if res.status_code in [201, 204]:
        inserted_tournaments += 1
print(f"✅ Inserted {inserted_tournaments} tournaments.")

# 6. Pull Leaderboards and Insert Results + Leaderboards
inserted_results = 0
inserted_leaderboards = 0

for t in filtered_tournaments:
    tid = t["TournamentID"]
    status = t["_status"]

    leaderboard_url = f"https://api.sportsdata.io/golf/v2/json/Leaderboard/{tid}"
    res = requests.get(leaderboard_url, headers=headers)

    if res.status_code != 200:
        print(f"⚠️ Skipping TID {tid}: {res.status_code}")
        continue

    data = res.json()
    players = data.get("Players", [])

    if not players:
        print(f"⚠️ No players for tournament {tid}")
        continue

    for p in players:
        result = {
            "tournament_id": tid,
            "player_id": p["PlayerID"],
            "position": p.get("Position"),
            "score": p.get("TotalScore"),
            "earnings": p.get("Earnings"),
            "round_1_score": p.get("Round1"),
            "round_2_score": p.get("Round2"),
            "round_3_score": p.get("Round3"),
            "round_4_score": p.get("Round4")
        }
        res_result = requests.post(f"{SUPABASE_URL}/results", headers=supabase_headers, json=result)
        if res_result.status_code in [201, 204]:
            inserted_results += 1

    # Insert leaderboard summary
    leaderboard_entry = {
        "event_id": tid,
        "sport": "golf",
        "status": status,
        "winner_id": players[0]["PlayerID"],
        "winning_score": players[0]["TotalScore"],
        "players_count": len(players)
    }
    res_leaderboard = requests.post(f"{SUPABASE_URL}/leaderboard", headers=supabase_headers, json=leaderboard_entry)
    if res_leaderboard.status_code in [201, 204]:
        inserted_leaderboards += 1

print(f"✅ Inserted {inserted_results} player results.")
print(f"✅ Inserted {inserted_leaderboards} tournament leaderboard summaries.")

