import requests

# Replace with your actual API key
API_KEY = "f3ed870496ea47b38c43a890c298bf5f"

# Set up request
url = "https://api.sportsdata.io/golf/v2/json/Players"
headers = {
    "Ocp-Apim-Subscription-Key": API_KEY
}

# Make the request
response = requests.get(url, headers=headers)

# Check for success
if response.status_code == 200:
    players = response.json()
    print(f"✅ {len(players)} players returned.")
    print(players[0])  # Preview the first player object
else:
    print(f"❌ API call failed: {response.status_code}")
    print(response.text)

import psycopg2

# Supabase DB connection details
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="D@t@-Rulez!10",
    host="db.iefmntaduuarxfyqbkds.supabase.co",
    port="5432"
)
cursor = conn.cursor()

# Loop through each player and insert into DB
for p in players:
    try:
        player_id = p["PlayerID"]
        name = f"{p['FirstName']} {p['LastName']}"
        country = p.get("Country", None)
        status = "Active"

        cursor.execute("""
            INSERT INTO players (player_id, full_name, country, status)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (player_id) DO NOTHING;
        """, (player_id, name, country, status))

    except Exception as e:
        print(f"❌ Error inserting player {p['PlayerID']}: {e}")

conn.commit()
cursor.close()
conn.close()
print("✅ All players inserted.")
