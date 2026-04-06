import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def get_standings():
    url = "https://api-web.nhle.com/v1/standings/now"
    response = requests.get(url)
    data = response.json()

    teams = []
    for team in data["standings"]:
        teams.append({
            "team": team["teamName"]["default"],
            "team_abbrev": team["teamAbbrev"]["default"],
            "conference": team["conferenceName"],
            "division": team["divisionName"],
            "games_played": team["gamesPlayed"],
            "wins": team["wins"],
            "losses": team["losses"],
            "ot_losses": team["otLosses"],
            "points": team["points"],
            "goal_diff": team["goalDifferential"],
            "home_wins": team["homeWins"],
            "away_wins": team["roadWins"],
            "row": team["regulationPlusOtWins"],
            "l10_wins": team["l10Wins"],
            "l10_losses": team["l10Losses"],
            "l10_ot_losses": team["l10OtLosses"]

        })
    df = pd.DataFrame(teams)
    df["last_updated"] = datetime.now().strftime("%B %d, %Y %I:%M %p")
    return df



# now to get remaining schedule
def get_remaining_schedule(team_abbrev):
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbrev}/now"
    response = requests.get(url)
    data = response.json()

    if response.status_code != 200 or not response.text:
        print(f"Warning: no data for {team_abbrev}")
        return []
    
    data = response.json()
    
    if "games" not in data:
        print(f"{team_abbrev} has no remaining games")
        return []

    games = []
    for game in data["games"]:
        if game["gameState"] == "FUT":
            games.append({
                "team": team_abbrev,
                "opponent": game["awayTeam"]["abbrev"] if game["homeTeam"]["abbrev"] == team_abbrev else game["homeTeam"]["abbrev"],
                "is_home": game["homeTeam"]["abbrev"] == team_abbrev,
                "date": game["gameDate"]

            })
    return games


def get_all_remaining_schedules(df):
    with ThreadPoolExecutor(max_workers=32) as executor:
        results = list(executor.map(get_remaining_schedule, df["team_abbrev"]))
    
    all_games = []
    for games in results:
        all_games.extend(games)
    
    schedule_df = pd.DataFrame(all_games)
    schedule_df = schedule_df.rename(columns={"team": "team_abbrev"})
    return schedule_df


# Test
if __name__ == "__main__":
    df = get_standings()
    schedule = get_all_remaining_schedules(df)
    print(schedule.head(20))
    print(schedule.shape)