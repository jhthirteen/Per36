import json
import datetime
import random
from nba_api.stats.endpoints import leaguedashplayerstats, playercareerstats, commonplayerinfo
import time 

HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive',
}

HISTORY_FILE = 'history.json'
DAILY_CACHE = 'daily_player.json'

def get_unique_daily_player():
    # 1. Load History
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"used_ids": [], "last_updated": ""}

    # 2. Get pool of current players (Added headers and timeout)
    print("Fetching player pool...")
    all_players_call = leaguedashplayerstats.LeagueDashPlayerStats(
        season='2025-26', 
        headers=HEADERS, 
        timeout=60
    )
    all_players = all_players_call.get_data_frames()[0]
    pool = all_players[all_players['MIN'] > 5] 

    # 3. Loop until we find a player not in history
    blacklisted_ids = {p['id'] for p in history['used_ids']}
    
    selected_player = None
    candidate = None
    while selected_player is None:
        candidate = pool.sample(n=1).iloc[0]
        if int(candidate['PLAYER_ID']) not in blacklisted_ids:
            selected_player = candidate

    player_id = int(selected_player['PLAYER_ID'])
    print(f"Selected: {selected_player['PLAYER_NAME']} ({player_id})")

    # Small delay so we don't spam
    time.sleep(2)

    # 4. Fetch the Biographical "ID Card" (Added headers)
    print("Fetching bio data...")
    bio = commonplayerinfo.CommonPlayerInfo(player_id=player_id, headers=HEADERS, timeout=60)
    bio_df = bio.get_data_frames()[0]
    
    time.sleep(2)

    # 5. Fetch the Stats (Current + Career) (Added headers)
    print("Fetching career stats...")
    career = playercareerstats.PlayerCareerStats(player_id=player_id, headers=HEADERS, timeout=60)
    career_df = career.get_data_frames()[0]

    # 6. Construct the Expanded JSON
    daily_data = {
        "date": str(datetime.date.today()),
        "player_id": player_id,
        "name": selected_player['PLAYER_NAME'],
        "bio": {
            "position": bio_df['POSITION'].iloc[0],
            "height": bio_df['HEIGHT'].iloc[0],
            "weight": bio_df['WEIGHT'].iloc[0],
            "school": bio_df['SCHOOL'].iloc[0],
            "draft_year": bio_df['DRAFT_YEAR'].iloc[0],
            "draft_round": bio_df['DRAFT_ROUND'].iloc[0],
            "draft_number": bio_df['DRAFT_NUMBER'].iloc[0],
            "jersey": bio_df['JERSEY'].iloc[0],
            "country": bio_df['COUNTRY'].iloc[0]
        },
        "current_season": selected_player.to_dict(),
        "career": career_df.to_dict(orient='records')
    }

    # 7. Save to history.json
    history['used_ids'].append({
        "date": daily_data['date'], 
        "id": daily_data['player_id'], 
        "name": daily_data['name']
    })
    history['last_updated'] = daily_data['date']
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

    # 8. Save to daily_player.json
    with open(DAILY_CACHE, 'w') as f:
        json.dump(daily_data, f, indent=4)

    print("Successfully updated daily player!")
    return daily_data

# Run the job
if __name__ == "__main__":
    get_unique_daily_player()