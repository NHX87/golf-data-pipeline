
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

years = [2024, 2025]
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

# 4. Fetch leaderboard + results + rounds + holes
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

    for p in players:
        result = {
            "tournament_id": tid,
            "player_id": p.get("PlayerID"),
            "position": p.get("Position"),
            "score": p.get("TotalScore"),
            "earnings": p.get("Earnings"),
            "round_1_score": p.get("Round1"),
            "round_2_score": p.get("Round2"),
            "round_3_score": p.get("Round3"),
            "round_4_score": p.get("Round4"),
            "player_tournament_id": p.get("PlayerTournamentID"),
            "total_strokes": p.get("TotalStrokes"),
            "fantasy_points": p.get("FantasyPoints"),
            "fedex_points": p.get("FedExPoints"),
            "made_cut": p.get("MadeCut"),
            "win": p.get("Win"),
            "position_description": p.get("TournamentStatus"),
            "created_at": datetime.utcnow().isoformat()
        }
        res_result = requests.post(f"{SUPABASE_URL}/results", headers=supabase_headers, json=result)
        if res_result.status_code in [201, 204]:
            inserted_results += 1

        for round in p.get("Rounds", []):
            round_data = {
                "player_tournament_id": p.get("PlayerTournamentID"),
                "round_number": round.get("Number"),
                "score": round.get("Score"),
                "tee_time": round.get("TeeTime"),
                "bogey_free": round.get("BogeyFree"),
                "birdies": round.get("Birdies"),
                "pars": round.get("Pars"),
                "bogeys": round.get("Bogeys"),
                "double_bogeys": round.get("DoubleBogeys"),
                "worse_than_double_bogey": round.get("WorseThanDoubleBogey"),
                "triple_bogeys": round.get("TripleBogeys"),
                "hole_in_ones": round.get("HoleInOnes"),
                "bounce_back_count": round.get("BounceBackCount"),
                "longest_birdie_streak": round.get("LongestBirdieOrBetterStreak"),
                "includes_five_plus_birdies": round.get("IncludesFiveOrMoreBirdiesOrBetter"),
                "player_id": p.get("PlayerID"),
                "created_at": datetime.utcnow().isoformat()
            }
            res_round = requests.post(f"{SUPABASE_URL}/player_rounds", headers=supabase_headers, json=round_data)

            for hole in round.get("Holes", []):
                hole_data = {
                    "player_round_id": round.get("PlayerRoundID"),
                    "hole_number": hole.get("Number"),
                    "par": hole.get("Par"),
                    "score": hole.get("Score"),
                    "to_par": hole.get("ToPar"),
                    "is_par": hole.get("IsPar"),
                    "birdie": hole.get("Birdie"),
                    "bogey": hole.get("Bogey"),
                    "double_bogey": hole.get("DoubleBogey"),
                    "worse_than_double_bogey": hole.get("WorseThanDoubleBogey"),
                    "hole_in_one": hole.get("HoleInOne"),
                    "eagle": hole.get("Eagle"),
                    "double_eagle": hole.get("DoubleEagle"),
                    "player_id": p.get("PlayerID")
                }
                requests.post(f"{SUPABASE_URL}/player_holes", headers=supabase_headers, json=hole_data)

    leaderboard_entry = {
        "tournament_id": tid,
        "sport": "golf",
        "status": "completed",
        "winner_id": players[0].get("PlayerID"),
        "winning_score": players[0].get("TotalScore"),
        "players_count": len(players),
        "updated_at": datetime.utcnow().isoformat()
    }
    res_leaderboard = requests.post(f"{SUPABASE_URL}/leaderboard", headers=supabase_headers, json=leaderboard_entry)
    if res_leaderboard.status_code in [201, 204]:
        inserted_leaderboards += 1

print(f"✅ Inserted {inserted_results} player results.")
print(f"✅ Inserted {inserted_leaderboards} tournament leaderboard summaries.")

