import requests
import os
from datetime import datetime

# Load environment variables
API_KEY = os.environ["SPORTSDATA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Headers
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
print("📡 Fetching players from SportsData.io...")
response = requests.get("https://api.sportsdata.io/golf/v2/json/Players", headers=headers)
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

# 3. Pull completed tournaments directly from SportsData.io
print("📡 Pulling completed tournaments directly from SportsData.io...")

years = [2023, 2024, 2025]
tournament_ids = []

for year in years:
    res = requests.get(f"https://api.sportsdata.io/golf/v2/json/Tournaments/{year}", headers=headers)
    if res.status_code != 200:
        print(f"⚠️ Failed to fetch tournaments for {year}: {res.status_code}")
        continue

    all_tournaments = res.json()
    for t in all_tournaments:
        if t.get("IsOver") is True:
            tournament_ids.append(t["TournamentID"])

print(f"✅ Retrieved {len(tournament_ids)} completed tournaments with results.")

# 4. Fetch leaderboard + results
inserted_results = 0
inserted_leaderboards = 0

for tid in tournament_ids:
    leaderboard_url = f"https://api.sportsdata.io/golf/v2/json/LeaderboardFinal/{tid}"
    res = requests.get(leaderboard_url, headers=headers)

    if res.status_code != 200:
        print(f"⚠️ Skipping TID {tid}: {res.status_code}")
        continue

    data = res.json()
    players = data.get("Players", [])

    if not players:
        print(f"⚠️ No players for tournament {tid}")
        continue

    # Insert player results
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
        "status": "completed",
        "winner_id": players[0]["PlayerID"],
        "winning_score": players[0]["TotalScore"],
        "players_count": len(players)
    }
    res_leaderboard = requests.post(f"{SUPABASE_URL}/leaderboard", headers=supabase_headers, json=leaderboard_entry)
    if res_leaderboard.status_code in [201, 204]:
        inserted_leaderboards += 1

print(f"✅ Inserted {inserted_results} player results.")
print(f"✅ Inserted {inserted_leaderboards} tournament leaderboard summaries.")
