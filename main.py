import requests
import os

# Load environment variables from GitHub secrets
API_KEY = os.environ["SPORTSDATA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Supabase headers
supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-conflict,return=minimal"
}

# Step 1: Fetch Players
print("📡 Fetching players from SportsData.io...")
player_url = "https://api.sportsdata.io/golf/v2/json/Players"
response = requests.get(player_url, headers={"Ocp-Apim-Subscription-Key": API_KEY})

if response.status_code != 200:
    print(f"❌ Failed to fetch players: {response.status_code} - {response.text}")
    exit(1)

players = response.json()
print(f"✅ Retrieved {len(players)} players.")

#Step 2: Insert Players into Database
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
    elif res.status_code != 409:
        # Silently ignore 409s, only show truly unexpected issues
        continue

print(f"🎉 Finished: {inserted_players} new players inserted.")

print("🚀 Moving on to tournament fetch...")

# Step 3: Fetch Tournaments
print("📡 Fetching tournaments from SportsData.io...")
tournament_url = "https://api.sportsdata.io/golf/v2/json/Tournaments/2024"
response = requests.get(tournament_url, headers={"Ocp-Apim-Subscription-Key": API_KEY})

if response.status_code != 200:
    print(f"❌ Failed to fetch tournaments: {response.status_code} - {response.text}")
    exit(1)

tournaments = response.json()
print(f"✅ Retrieved {len(tournaments)} tournaments.")
print(f"🔍 Sample tournament: {tournaments[0] if tournaments else 'No tournaments returned'}")

# Step 3b: Fetch 2025 Tournaments
print("📡 Fetching 2025 tournaments from SportsData.io...")
tournament_url_2025 = "https://api.sportsdata.io/golf/v2/json/Tournaments/2025"
response_2025 = requests.get(tournament_url_2025, headers={"Ocp-Apim-Subscription-Key": API_KEY})

if response_2025.status_code != 200:
    print(f"❌ Failed to fetch 2025 tournaments: {response_2025.status_code} - {response_2025.text}")
else:
    tournaments_2025 = response_2025.json()
    print(f"✅ Retrieved {len(tournaments_2025)} tournaments for 2025.")
    tournaments += tournaments_2025  # combine with 2024 data

# Step 4: Insert Tournaments into Supabase
inserted_tournaments = 0
for t in tournaments:
    data = {
        "tournament_id": t["TournamentID"],
        "name": t["Name"],
        "tour": t.get("Tour", None),
        "start_date": t.get("StartDate", None),
        "end_date": t.get("EndDate", None),
        "location": t.get("Location", None)
    }

    res = requests.post(f"{SUPABASE_URL}/tournaments", headers=supabase_headers, json=[data])
    if res.status_code in [201, 204]:
        inserted_tournaments += 1
    elif res.status_code != 409:
        print(f"⚠️ Failed to insert tournament {data['tournament_id']}: {res.status_code} - {res.text}")

print(f"✅ Finished inserting {inserted_tournaments} new tournaments.")

from datetime import datetime


# Step 5: Fetch leaderboard data

print("📊 Fetching tournament IDs for results from Supabase...")
res = requests.get(
    f"{SUPABASE_URL}/tournaments?select=tournament_id,start_date&start_date=gte.2024-01-01",
    headers=supabase_headers
)

if res.status_code != 200:
    print(f"❌ Failed to fetch tournament IDs from Supabase: {res.status_code} - {res.text}")
    tournament_ids = []
else:
    supabase_tournaments = res.json()
    tournament_ids = [t["tournament_id"] for t in supabase_tournaments]

print(f"🔁 Attempting leaderboard pulls for {len(tournament_ids)} tournaments...")


inserted_results = 0

for tid in tournament_ids:
    leaderboard_url = f"https://api.sportsdata.io/golf/v2/json/Leaderboard/{tid}"
    res = requests.get(leaderboard_url, headers={"Ocp-Apim-Subscription-Key": API_KEY})

    if res.status_code != 200:
        print(f"⚠️ Skipping TID {tid} (no leaderboard yet): {res.status_code}")
        continue

    data = res.json()
    players = data.get("Players", [])
    
    if not players:
        print(f"⚠️ No player results for tournament {tid}")
        continue

    for p in players:
        result = {
            "tournament_id": tid,
            "player_id": p["PlayerID"],
            "position": p.get("Position", None),
            "total_score": p.get("TotalScore", None),
            "round1": p.get("Round1", None),
            "round2": p.get("Round2", None),
            "round3": p.get("Round3", None),
            "round4": p.get("Round4", None),
            "earnings": p.get("Earnings", None)
        }

        res_insert = requests.post(f"{SUPABASE_URL}/results", headers=supabase_headers, json=result)
        if res_insert.status_code in [201, 204]:
            inserted_results += 1
        elif res_insert.status_code != 409:
            print(f"❌ Insert error for player {p['PlayerID']} in TID {tid}: {res_insert.status_code} - {res_insert.text}")

print(f"✅ Inserted {inserted_results} leaderboard rows.")
