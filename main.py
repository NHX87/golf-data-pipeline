import requests
import os

# Load secrets from GitHub Actions environment variables
API_KEY = os.environ["SPORTSDATA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Step 1: Get player data from SportsData.io
url = "https://api.sportsdata.io/golf/v2/json/Players"
headers = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

response = requests.get(url, headers=headers)
if response.status_code != 200:
    print(f"❌ API error: {response.status_code} - {response.text}")
    exit()

players = response.json()

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

    res = requests.post(f"{SUPABASE_URL}/players", headers=supabase_headers, json=[data])
    if res.status_code in [201, 204]:
        inserted += 1
    else:
        print(f"⚠️ Failed to insert player {p['PlayerID']}: {res.status_code} - {res.text}")

print(f"✅ Inserted {inserted} players.")
