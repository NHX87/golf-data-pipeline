import requests
import os

# Load environment variables from GitHub secrets
API_KEY = os.environ["SPORTSDATA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Step 1: Call the SportsData.io Players API
print("📡 Fetching players from SportsData.io...")
url = "https://api.sportsdata.io/golf/v2/json/Players"
headers = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch players: {response.status_code} - {response.text}")
    exit(1)

players = response.json()
print(f"✅ Retrieved {len(players)} players.")

# Step 2: Insert into Supabase using REST API
supabase_headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates, return=minimal"
}

inserted = 0
for p in players:
    data = {
        "player_id": p["PlayerID"],
        "full_name": f"{p['FirstName']} {p['LastName']}",
        "country": p.get("Country"),
        "status": "Active"
    }

    print(f"📥 Inserting: {data['full_name']} ({data['player_id']})")

    res = requests.post(f"{SUPABASE_URL}/players", headers=supabase_headers, json=[data])
    if res.status_code in [201, 204]:
        inserted += 1
    else:
        print(f"⚠️ Failed to insert {data['player_id']}: {res.status_code} - {res.text}")

print(f"🎉 Finished: {inserted} players inserted successfully.")

# Step 3: Call the SportsData.io Tournament API 
print("📡 Fetching tournaments from SportsData.io...")
url = "https://api.sportsdata.io/golf/v2/json/Tournaments/2024"
headers = {
    "Ocp-Apim-Subscription-Key": API_KEY
}
response = requests.get(url, headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to fetch tournaments: {response.status_code} - {response.text}")
    exit(1)

tournaments = response.json()
print(f"✅ Retrieved {len(tournaments)} tournaments.")
print(f"🔍 Sample tournament: {tournaments[0] if tournaments else 'No tournaments returned'}")
print(f"🔁 Attempting to insert {len(tournaments)} tournaments...")

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

    print(f"📅 Inserting tournament: {data['name']} ({data['tournament_id']})")

    res = requests.post(f"{SUPABASE_URL}/tournaments", headers=supabase_headers, json=[data])
    if res.status_code in [201, 204]:
        inserted_tournaments += 1
    else:
        print(f"⚠️ Failed to insert tournament {data['tournament_id']}: {res.status_code} - {res.text}")

print(f"✅ Finished inserting {inserted_tournaments} tournaments.")

    res = requests.post(f"{SUPABASE_URL}/tournaments", headers=supabase_headers, json=[data])
    if res.status_code in [201, 204]:
        inserted_tournaments += 1
    else:
        print(f"⚠️ Failed to insert tournament {data['tournament_id']}: {res.status_code} - {res.text}")

print(f"✅ Finished inserting {inserted_tournaments} tournaments.")

