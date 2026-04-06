import panel as pn
import pandas as pd
from data.fetch_data import get_standings, get_all_remaining_schedules
from data.process_data import add_team_metrics, add_ranking, simulate_season

pn.extension('tabulator', theme="dark")

# ── Loading screen ──────────────────────────────────────────
loading = pn.indicators.LoadingSpinner(value=True, size=50)
main_content = pn.Column(
    "# NHL Playoff Simulations",
    "### Loading latest NHL data... this may take up to 30 seconds",
    loading
)

# ── Helper functions ────────────────────────────────────────
def color_rows(row):
    if row["Div Rank"] <= 3:
        return ["background-color: rgba(26, 71, 42, 0.6); color: white"] * len(row)
    elif row["WC Rank"] <= 5:
        return ["background-color: rgba(122, 92, 0, 0.6); color: white"] * len(row)
    else:
        return ["background-color: rgba(107, 26, 26, 0.6); color: white"] * len(row)

def make_table(data):
    data = data.copy()
    # Store raw float in hidden column for coloring
    data["_prob"] = data["Playoff %"]
    # Convert to percentage string for display
    data["Playoff %"] = (data["Playoff %"] * 100).round(1).astype(str) + "%"
    # Apply colors using hidden column
    styled = data.style.apply(color_rows, axis=1)
    return pn.widgets.Tabulator(
    styled,
    pagination="local",
    page_size=20,
    sizing_mode="stretch_width",
    theme="midnight",
    hidden_columns=["WC Rank", "_prob"]
)

def make_display_df(data):
    df = data[[
        "team", "points", "division", "division_rank", "wildcard_rank", "playoff_prob"
    ]].copy()
    df.columns = ["Team", "Points", "Division", "Div Rank", "WC Rank", "Playoff %"]
    df["WC Rank"] = df["WC Rank"].fillna(999)
    df = df.reset_index(drop=True)
    return df

# ── Data loading ─────────────────────────────────────────────
def load_data():
    df = get_standings()
    df = add_team_metrics(df)
    df = add_ranking(df)
    schedule = get_all_remaining_schedules(df)
    probs = simulate_season(df, schedule)
    df = df.merge(probs, on="team_abbrev", how="left")

    display_df = make_display_df(df)

    all_table = make_table(display_df.drop(columns="Division").sort_values("Playoff %", ascending=False))

    atlantic_table = make_table(display_df[display_df["Division"] == "Atlantic"].drop(columns="Division").sort_values("Div Rank"))
    metro_table = make_table(display_df[display_df["Division"] == "Metropolitan"].drop(columns="Division").sort_values("Div Rank"))
    central_table = make_table(display_df[display_df["Division"] == "Central"].drop(columns="Division").sort_values("Div Rank"))
    pacific_table = make_table(display_df[display_df["Division"] == "Pacific"].drop(columns="Division").sort_values("Div Rank"))

    dashboard = pn.Tabs(
        ("All Teams", pn.Column("## All Teams", all_table)),
        ("Atlantic", pn.Column("## Atlantic Division", atlantic_table)),
        ("Metropolitan", pn.Column("## Metropolitan Division", metro_table)),
        ("Central", pn.Column("## Central Division", central_table)),
        ("Pacific", pn.Column("## Pacific Division", pacific_table)),
        styles={"background": "#1a1a2e", "padding": "20px"}
    )

    main_content.clear()
    main_content.append(dashboard)
    print("Dashboard loaded!")

pn.state.onload(load_data)
main_content.servable()