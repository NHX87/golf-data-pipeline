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
