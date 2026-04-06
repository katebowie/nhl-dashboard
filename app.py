import pandas as pd
import streamlit as st
from data.fetch_data import get_standings, get_all_remaining_schedules
from data.process_data import add_team_metrics, add_ranking, simulate_season

st.set_page_config(
    page_title="NHL Playoff Simulations",
    page_icon="🏒",
    layout="wide"
)

st.title("NHL Playoff Simulations")

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
    data["Playoff %"] = (data["Playoff %"] * 100).round(1).astype(str) + "%"
    display_cols = [c for c in data.columns if c != "WC Rank"]
    styled = data.style.apply(color_rows, axis=1)
    st.dataframe(styled, column_order=display_cols, use_container_width=True)

def make_display_df(data):
    df = data[[
        "team", "points", "division", "division_rank", "wildcard_rank", "playoff_prob"
    ]].copy()
    df.columns = ["Team", "Points", "Division", "Div Rank", "WC Rank", "Playoff %"]
    df["WC Rank"] = df["WC Rank"].fillna(999)
    df = df.reset_index(drop=True)
    return df

# ── Data loading ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    df = get_standings()
    df = add_team_metrics(df)
    df = add_ranking(df)
    schedule = get_all_remaining_schedules(df)
    probs = simulate_season(df, schedule)
    df = df.merge(probs, on="team_abbrev", how="left")
    return df

with st.spinner("Loading latest NHL data... this may take up to 30 seconds"):
    df = load_data()

display_df = make_display_df(df)

# --- Tabs --------------------------------------
all_tab, atlantic_tab, metro_tab, central_tab, pacific_tab = st.tabs([
    "All Teams", "Atlantic", "Metropolitan", "Central", "Pacific"
])

with all_tab:
    st.subheader("All Teams")
    data = display_df.drop(columns="Division").sort_values("Playoff %", ascending=False)
    make_table(data)

with atlantic_tab:
    st.subheader("Atlantic Division")
    data = display_df[display_df["Division"] == "Atlantic"].drop(columns="Division").sort_values("Div Rank")
    make_table(data)

with metro_tab:
    st.subheader("Metropolitan Division")
    data = display_df[display_df["Division"] == "Metropolitan"].drop(columns="Division").sort_values("Div Rank")
    make_table(data)

with central_tab:
    st.subheader("Central Division")
    data = display_df[display_df["Division"] == "Central"].drop(columns="Division").sort_values("Div Rank")
    make_table(data)

with pacific_tab:
    st.subheader("Pacific Division")
    data = display_df[display_df["Division"] == "Pacific"].drop(columns="Division").sort_values("Div Rank")
    make_table(data)