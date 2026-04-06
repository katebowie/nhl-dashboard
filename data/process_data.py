import pandas as pd
import numpy as np
from data.fetch_data import get_standings, get_all_remaining_schedules

def add_ranking(df, points_col="points"):
    df["division_rank"] = df.sort_values(
        ["division", points_col, "games_played", "row", "goal_diff"],
        ascending=[True, False, True, False, False]
    ).groupby("division").cumcount() + 1

    df["clinches_division"] = df["division_rank"] <= 3

    non_division = df[~df["clinches_division"]].copy()
    non_division["wildcard_rank"] = non_division.sort_values(
        ["conference", points_col, "games_played", "row", "goal_diff"],
        ascending=[True, False, True, False, False]
    ).groupby("conference").cumcount() + 1

    df = df.merge(non_division[["team_abbrev", "wildcard_rank"]], on="team_abbrev", how="left")

    # in play-offs
    df["in_playoffs"] = (df["clinches_division"]) | (df["wildcard_rank"] <= 2)

    return df


# Add "strength" and other metrics
def add_team_metrics(df):
    # add hot streak
    df["streak"] = ((df["l10_wins"] * 2) + (df["l10_ot_losses"]))/20

    # add points percentage
    df["points_perc"] = df["points"]/(df["games_played"]*2)
    df["strength"] = (df["points_perc"]*0.7) + (df["streak"]*0.3)
    return df


# Simulate!
def simulate_season(df, schedule, n_simulations = 500):
    strengths = df.set_index("team_abbrev")["strength"].to_dict()

    # tracking how many times teams make it
    playoff_counts = {abbrev: 0 for abbrev in df["team_abbrev"]}

    for i in range(n_simulations):
        sim_points = df.set_index("team_abbrev")["points"].to_dict()

        # simulate remaining games
        for x, game in schedule.iterrows():
            home = game["team_abbrev"]
            away = game["opponent"]

            # grab strengths
            home_strength = strengths.get(home, 0.5)
            away_strength = strengths.get(away,0.5)

            # home ice adv
            home_strength *= 1.05

            # win prob for home team
            home_win_prob = home_strength / (home_strength + away_strength)

            # simulate winner and give 2pts
            if np.random.random() < home_win_prob:
                winner, loser = home, away
            else:
                winner, loser = away, home

            # 25% chance game goes to OT
            if np.random.random() < 0.25:
                sim_points[winner] = sim_points.get(winner, 0) + 2
                sim_points[loser] = sim_points.get(loser, 0) + 1
            else:
                sim_points[winner] = sim_points.get(winner, 0) + 2
            
        # Build simulated standings df
        sim_df = pd.DataFrame(list(sim_points.items()), columns = ["team_abbrev", "sim_points"])
        sim_df = sim_df.merge(
            df[["team_abbrev", "conference", "division", "games_played", "row", "goal_diff"]], on="team_abbrev")
        
        sim_df = add_ranking(sim_df, points_col="sim_points")

        # count playoff appearances
        for _, team in sim_df[sim_df["in_playoffs"]].iterrows():
            playoff_counts[team["team_abbrev"]] += 1

    playoff_probs = {team: count / n_simulations for team, count in playoff_counts.items()}

    return pd.DataFrame(list(playoff_probs.items()), columns = ["team_abbrev", "playoff_prob"])


# Test
if __name__ == "__main__":
    df = get_standings()
    df = add_team_metrics(df)
    df = add_ranking(df)
    schedule = get_all_remaining_schedules(df)
    probs = simulate_season(df, schedule)
    df = df.merge(probs, on="team_abbrev", how="left")
    print(probs.sort_values("playoff_prob", ascending=False))
