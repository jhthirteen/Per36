import json
import datetime
import random
from nba_api.stats.endpoints import leaguedashplayerstats, playercareerstats, commonplayerinfo

HISTORY_FILE = 'history.json'
DAILY_CACHE = 'daily_player.json'

def get_unique_daily_player():
    # 1. Load History
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {"used_ids": [], "last_updated": ""}

    # 2. Get pool of current players (using your existing logic)
    # Note: Use season='2025-26' as requested
    all_players = leaguedashplayerstats.LeagueDashPlayerStats(season='2025-26').get_data_frames()[0]
    pool = all_players[all_players['MIN'] > 5] # Narrowing to keep it fun/guessable

    # 3. Loop until we find a player not in history
    blacklisted_ids = {p['id'] for p in history['used_ids']}
    
    selected_player = None
    while selected_player is None:
        candidate = pool.sample(n=1).iloc[0]
        if candidate['PLAYER_ID'] not in blacklisted_ids:
            selected_player = candidate

    player_id = int(candidate['PLAYER_ID'])

    # 2. Fetch the Biographical "ID Card"
    bio = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
    bio_df = bio.get_data_frames()[0] # The 'CommonPlayerInfo' table
    
    # 3. Fetch the Stats (Current + Career)
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_df = career.get_data_frames()[0]

    # 4. Construct the Expanded JSON
    daily_data = {
        "date": str(datetime.date.today()),
        "player_id": player_id,
        "name": candidate['PLAYER_NAME'],
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
        "current_season": candidate.to_dict(),
        "career": career_df.to_dict(orient='records')
    }

    # 6. Save to history.json (the permanent log)
    history['used_ids'].append({
        "date": daily_data['date'], 
        "id": daily_data['player_id'], 
        "name": daily_data['name']
    })
    history['last_updated'] = daily_data['date']
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

    # 7. Save to daily_player.json (the current game's cache)
    with open(DAILY_CACHE, 'w') as f:
        json.dump(daily_data, f, indent=4)

    return daily_data

# Run the job
get_unique_daily_player()