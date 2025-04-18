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
    "Prefer": "resolution=merge-duplicates"
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
