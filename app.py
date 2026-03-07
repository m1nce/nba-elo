import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, no_update, ctx

from NBARater import NBARater
from NBAScraper import NBAScraper

DB_PATH = Path("data") / "nba.db"
PAGE_SIZE = 25


# ── Team Metadata ──────────────────────────────────────────────────────────────

TEAM_META = {
    "Atlanta Hawks":           {"abbrev": "atl",  "primary": "#E03A3E", "secondary": "#C1D32F"},
    "Boston Celtics":          {"abbrev": "bos",  "primary": "#007A33", "secondary": "#BA9653"},
    "Brooklyn Nets":           {"abbrev": "bkn",  "primary": "#000000", "secondary": "#AAAAAA"},
    "Charlotte Hornets":       {"abbrev": "cha",  "primary": "#00788C", "secondary": "#1D1160"},
    "Chicago Bulls":           {"abbrev": "chi",  "primary": "#CE1141", "secondary": "#000000"},
    "Cleveland Cavaliers":     {"abbrev": "cle",  "primary": "#860038", "secondary": "#FDBB30"},
    "Dallas Mavericks":        {"abbrev": "dal",  "primary": "#00538C", "secondary": "#002F5F"},
    "Denver Nuggets":          {"abbrev": "den",  "primary": "#0E2240", "secondary": "#FEC524"},
    "Detroit Pistons":         {"abbrev": "det",  "primary": "#C8102E", "secondary": "#006BB6"},
    "Golden State Warriors":   {"abbrev": "gsw",  "primary": "#1D428A", "secondary": "#FFC72C"},
    "Houston Rockets":         {"abbrev": "hou",  "primary": "#CE1141", "secondary": "#000000"},
    "Indiana Pacers":          {"abbrev": "ind",  "primary": "#002D62", "secondary": "#FDBB30"},
    "Los Angeles Clippers":    {"abbrev": "lac",  "primary": "#C8102E", "secondary": "#1D428A"},
    "Los Angeles Lakers":      {"abbrev": "lal",  "primary": "#552583", "secondary": "#FDB927"},
    "Memphis Grizzlies":       {"abbrev": "mem",  "primary": "#5D76A9", "secondary": "#12173F"},
    "Miami Heat":              {"abbrev": "mia",  "primary": "#98002E", "secondary": "#F9A01B"},
    "Milwaukee Bucks":         {"abbrev": "mil",  "primary": "#00471B", "secondary": "#EEE1C6"},
    "Minnesota Timberwolves":  {"abbrev": "min",  "primary": "#0C2340", "secondary": "#236192"},
    "New Orleans Pelicans":    {"abbrev": "no",   "primary": "#0C2340", "secondary": "#C8102E"},
    "New York Knicks":         {"abbrev": "nyk",  "primary": "#006BB6", "secondary": "#F58426"},
    "Oklahoma City Thunder":   {"abbrev": "okc",  "primary": "#007AC1", "secondary": "#EF3B24"},
    "Orlando Magic":           {"abbrev": "orl",  "primary": "#0077C0", "secondary": "#C4CED4"},
    "Philadelphia 76ers":      {"abbrev": "phi",  "primary": "#006BB6", "secondary": "#ED174C"},
    "Phoenix Suns":            {"abbrev": "phx",  "primary": "#1D1160", "secondary": "#E56020"},
    "Portland Trail Blazers":  {"abbrev": "por",  "primary": "#E03A3E", "secondary": "#000000"},
    "Sacramento Kings":        {"abbrev": "sac",  "primary": "#5A2D81", "secondary": "#63727A"},
    "San Antonio Spurs":       {"abbrev": "sas",  "primary": "#000000", "secondary": "#C4CED4"},
    "Toronto Raptors":         {"abbrev": "tor",  "primary": "#CE1141", "secondary": "#000000"},
    "Utah Jazz":               {"abbrev": "utah", "primary": "#002B5C", "secondary": "#F9A01B"},
    "Washington Wizards":      {"abbrev": "wsh",  "primary": "#002B5C", "secondary": "#E31837"},
}


ERAS = [
    {"id": "all",    "label": "All Time",           "start": 1975, "end": 9999},
    {"id": "bird",   "label": "Bird / Magic 79–91", "start": 1979, "end": 1991},
    {"id": "jordan", "label": "Jordan 91–98",        "start": 1991, "end": 1998},
    {"id": "kobe",   "label": "Kobe Era 96–16",      "start": 1996, "end": 2016},
    {"id": "lebron", "label": "LeBron 03–now",        "start": 2003, "end": 9999},
    {"id": "last5",  "label": "Last 5 Yrs",           "start": -5,   "end": 9999},
]


def logo_url(team_name: str) -> str:
    abbrev = TEAM_META.get(team_name, {}).get("abbrev", "")
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbrev}.png" if abbrev else ""


def team_primary(team_name: str) -> str:
    return TEAM_META.get(team_name, {}).get("primary", "#333333")


def get_current_season() -> int:
    today = date.today()
    return today.year if today.month >= 10 else today.year - 1


def get_team_elo(team_name: str, teams_dict: dict) -> float:
    normalized = NBARater.map_team_names(team_name)
    return float(teams_dict[normalized][-1]) if normalized in teams_dict else 1200.0


# ── Data loading ───────────────────────────────────────────────────────────────

def load_and_simulate():
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql(
        "SELECT * FROM games "
        "WHERE visitor_points IS NOT NULL AND home_points IS NOT NULL "
        "ORDER BY date ASC",
        conn,
    )
    conn.close()

    df["Win"] = (df["visitor_points"] > df["home_points"]).astype(float)
    df["Date"] = df["date"]
    df["Visitor"] = df["visitor"]
    df["Home"] = df["home"]
    df["Notes"] = df["notes"].fillna("")

    rater = NBARater()
    rater.eloSimulator(df)
    teams = rater.getTeams()
    game_log = rater.getGameLog()

    records = []
    for _, row in game_log.iterrows():
        records.append({"team": row["visitor"], "date": row["date"], "elo": row["visitor_after"]})
        records.append({"team": row["home"], "date": row["date"], "elo": row["home_after"]})
    team_series = pd.DataFrame(records)
    team_series["date"] = pd.to_datetime(team_series["date"])

    return teams, game_log, team_series


# ── Startup data ───────────────────────────────────────────────────────────────

TEAMS, GAME_LOG, TEAM_SERIES = load_and_simulate()
ALL_TEAMS = sorted(TEAMS.keys())
CURRENT_SEASON = get_current_season()
SEASONS_AVAIL = ["All"] + [str(s) for s in sorted(GAME_LOG["season"].unique(), reverse=True)]
UPCOMING_DF = NBAScraper().scrape_upcoming(days=7)


# ── Static content builders ────────────────────────────────────────────────────

def build_elo_figure(era_id: str = "all") -> go.Figure:
    era = next((e for e in ERAS if e["id"] == era_id), ERAS[0])
    start_year = CURRENT_SEASON - 4 if era["start"] == -5 else era["start"]
    end_year = CURRENT_SEASON if era["end"] == 9999 else era["end"]

    fig = go.Figure()
    for team in ALL_TEAMS:
        ts = TEAM_SERIES[TEAM_SERIES["team"] == team].sort_values("date")
        ts = ts[ts["date"].dt.year.between(start_year, end_year)]
        fig.add_trace(
            go.Scatter(
                x=ts["date"],
                y=ts["elo"],
                mode="lines",
                name=team,
                line=dict(width=1.5, color=team_primary(team)),
                hovertemplate=f"<b>{team}</b><br>%{{x|%b %d, %Y}}: %{{y:.1f}}<extra></extra>",
            )
        )
    fig.update_layout(
        height=500,
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=dict(title="Date", rangeslider=dict(visible=True), type="date"),
        yaxis=dict(title="ELO Rating"),
        legend=dict(orientation="v", x=1.01, y=1, font=dict(size=10)),
        hovermode="closest",
        margin=dict(l=50, r=200, t=30, b=100),
    )
    return fig


def build_standings_table() -> dbc.Table:
    season_log = GAME_LOG[GAME_LOG["season"] == CURRENT_SEASON]
    rows = []
    for team in ALL_TEAMS:
        current_elo = float(TEAMS[team][-1])
        team_games = season_log[(season_log["visitor"] == team) | (season_log["home"] == team)]
        if not team_games.empty:
            first = team_games.iloc[0]
            start_elo = float(
                first["visitor_before"] if first["visitor"] == team else first["home_before"]
            )
        else:
            start_elo = current_elo
        rows.append({
            "Team": team,
            "Current ELO": round(current_elo, 1),
            "Delta": round(current_elo - start_elo, 1),
        })

    rows.sort(key=lambda r: r["Current ELO"], reverse=True)

    table_rows = []
    for rank, r in enumerate(rows, 1):
        delta = r["Delta"]
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        delta_color = "#198754" if delta > 0 else ("#dc3545" if delta < 0 else "#6c757d")
        table_rows.append(html.Tr([
            html.Td(rank, className="text-muted"),
            html.Td(html.Img(src=logo_url(r["Team"]), style={"height": "28px"})),
            html.Td(r["Team"], style={"fontWeight": "600"}),
            html.Td(f'{r["Current ELO"]:.1f}'),
            html.Td(delta_str, style={"color": delta_color, "fontWeight": "600"}),
        ]))

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Rank"), html.Th(""), html.Th("Team"),
                html.Th("ELO"), html.Th("Δ Season"),
            ])),
            html.Tbody(table_rows),
        ],
        bordered=False, hover=True, responsive=True, striped=True, size="sm",
    )


def build_upcoming_content():
    if UPCOMING_DF is None or UPCOMING_DF.empty:
        return dbc.Alert("No upcoming games found in the next 7 days.", color="info")

    table_rows = []
    for _, row in UPCOMING_DF.iterrows():
        v_name = NBARater.map_team_names(row["visitor"])
        h_name = NBARater.map_team_names(row["home"])
        prob_v = NBARater.expectedResult(get_team_elo(row["visitor"], TEAMS), get_team_elo(row["home"], TEAMS))
        table_rows.append(html.Tr([
            html.Td(row["date"]),
            html.Td(html.Img(src=logo_url(v_name), style={"height": "24px"})),
            html.Td(row["visitor"]),
            html.Td(html.Img(src=logo_url(h_name), style={"height": "24px"})),
            html.Td(row["home"]),
            html.Td(f"{prob_v:.1%}"),
            html.Td(f"{1 - prob_v:.1%}"),
        ]))

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Date"), html.Th(""), html.Th("Visitor"),
                html.Th(""), html.Th("Home"),
                html.Th("Visitor Win Prob"), html.Th("Home Win Prob"),
            ])),
            html.Tbody(table_rows),
        ],
        bordered=False, hover=True, responsive=True, striped=True, size="sm",
    )


def _game_log_table(df: pd.DataFrame) -> dbc.Table:
    """Renders a game log DataFrame as a styled dbc.Table with logos."""
    table_rows = []
    for _, row in df.iterrows():
        v_delta = row["visitor_delta"]
        h_delta = row["home_delta"]
        notes = row["notes"] if pd.notna(row.get("notes", "")) else ""
        table_rows.append(html.Tr([
            html.Td(row["date"]),
            html.Td(html.Img(src=logo_url(row["visitor"]), style={"height": "24px"})),
            html.Td(row["visitor"]),
            html.Td(html.Img(src=logo_url(row["home"]), style={"height": "24px"})),
            html.Td(row["home"]),
            html.Td(row["result"]),
            html.Td(f"{v_delta:+.1f}"),
            html.Td(f"{h_delta:+.1f}"),
            html.Td(f'{row["win_prob_visitor"] * 100:.1f}%'),
            html.Td(notes),
        ]))

    return dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("Date"), html.Th(""), html.Th("Visitor"),
                html.Th(""), html.Th("Home"), html.Th("Result"),
                html.Th("Visitor ELO Δ"), html.Th("Home ELO Δ"),
                html.Th("Visitor Win Prob"), html.Th("Notes"),
            ])),
            html.Tbody(table_rows),
        ],
        bordered=False, hover=True, responsive=True, striped=True, size="sm",
    )


# ── Pre-build static content ───────────────────────────────────────────────────

STANDINGS_TABLE = build_standings_table()
UPCOMING_CONTENT = build_upcoming_content()

team_options = [{"label": t, "value": t} for t in ALL_TEAMS]
season_options = [
    {"label": s if s != "All" else "All Seasons", "value": s}
    for s in SEASONS_AVAIL
]


# ── App ────────────────────────────────────────────────────────────────────────

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="NBA ELO Dashboard",
)

app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        "🏀 NBA ELO",
                        style={"fontFamily": "Oswald, sans-serif", "letterSpacing": "2px"},
                    )
                ),
                dbc.Col(
                    dbc.Button(
                        "Refresh Data",
                        id="refresh-btn",
                        color="secondary",
                        outline=True,
                        size="sm",
                    ),
                    width="auto",
                    className="d-flex align-items-center ms-auto",
                ),
            ],
            className="my-3 align-items-center",
        ),

        dcc.Store(id="hist-page", data=0),
        dcc.Input(id="dnd-event", value="", style={"display": "none"}),
        dcc.Store(id="wp-visitor-store", data=ALL_TEAMS[0]),
        dcc.Store(id="wp-home-store",    data=ALL_TEAMS[1]),
        dcc.Store(id="h2h-filter-store", data=10),

        dbc.Tabs(
            [
                dbc.Tab(
                    label="ELO & Standings",
                    tab_id="elo",
                    children=[
                        dbc.Row([
                            dbc.Col(
                                html.Div([
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                e["label"],
                                                id=f"era-btn-{e['id']}",
                                                size="sm",
                                                color="primary" if e["id"] == "all" else "secondary",
                                                outline=e["id"] != "all",
                                                className="era-btn",
                                            )
                                            for e in ERAS
                                        ],
                                        className="mb-2",
                                    ),
                                    dcc.Graph(id="elo-chart", config={"displayModeBar": False}),
                                ]),
                                md=8,
                            ),
                            dbc.Col(
                                [
                                    html.H5(
                                        "Current Standings",
                                        style={"fontFamily": "Oswald, sans-serif", "letterSpacing": "1px"},
                                    ),
                                    html.Div(
                                        STANDINGS_TABLE,
                                        style={"overflowY": "auto", "maxHeight": "520px"},
                                    ),
                                ],
                                md=4,
                            ),
                        ]),
                    ],
                ),
                dbc.Tab(
                    label="Match-up",
                    tab_id="matchup",
                    children=[
                        # Team picker grid
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Img(
                                            src=logo_url(team),
                                            style={"height": "36px", "pointerEvents": "none"},
                                        ),
                                        html.Div(
                                            TEAM_META[team]["abbrev"].upper(),
                                            style={"fontSize": "0.65rem", "marginTop": "4px", "pointerEvents": "none"},
                                        ),
                                    ],
                                    className="team-tile",
                                    draggable="true",
                                    **{"data-team": team},
                                )
                                for team in ALL_TEAMS
                            ],
                            className="team-picker",
                        ),
                        # Drop zones row
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div("VISITOR", className="dnd-slot-label"),
                                        html.Div(
                                            id="drop-visitor",
                                            className="dnd-slot",
                                            **{"data-slot": "visitor"},
                                        ),
                                    ],
                                    md=5,
                                ),
                                dbc.Col(
                                    html.Div(
                                        "VS",
                                        className="text-center fw-bold text-muted",
                                        style={"fontFamily": "Oswald, sans-serif", "fontSize": "1.2rem",
                                               "lineHeight": "130px"},
                                    ),
                                    md=2,
                                ),
                                dbc.Col(
                                    [
                                        html.Div("HOME", className="dnd-slot-label"),
                                        html.Div(
                                            id="drop-home",
                                            className="dnd-slot",
                                            **{"data-slot": "home"},
                                        ),
                                    ],
                                    md=5,
                                ),
                            ],
                            className="mb-3",
                        ),
                        dbc.Row(
                            dbc.Col(
                                html.Div(
                                    [
                                        html.Span("Show:", className="h2h-segment-label"),
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("Last 5",  id="h2h-filter-5",  size="sm", color="secondary", outline=True),
                                                dbc.Button("Last 10", id="h2h-filter-10", size="sm", color="primary",   outline=False),
                                                dbc.Button("Last 20", id="h2h-filter-20", size="sm", color="secondary", outline=True),
                                                dbc.Button("All",     id="h2h-filter-all", size="sm", color="secondary", outline=True),
                                            ],
                                            className="h2h-segment",
                                        ),
                                    ],
                                    className="h2h-segment-wrap",
                                ),
                                className="text-center",
                            ),
                            className="mb-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(html.Div(id="matchup-scoreboard"), md=5),
                                dbc.Col(dcc.Graph(id="matchup-chart"), md=7),
                            ],
                            className="mb-3",
                        ),
                        html.Div(id="matchup-record"),
                        html.Div(id="matchup-h2h-table"),
                    ],
                ),
                dbc.Tab(
                    label="Match History",
                    tab_id="history",
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="hist-team",
                                        options=[{"label": "All Teams", "value": "All"}] + team_options,
                                        value="All",
                                        clearable=False,
                                    ),
                                    md=6,
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id="hist-season",
                                        options=season_options,
                                        value="All",
                                        clearable=False,
                                    ),
                                    md=6,
                                ),
                            ],
                            className="mb-3",
                        ),
                        html.Div(id="hist-table"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Button(
                                        "← Prev",
                                        id="hist-prev",
                                        color="secondary",
                                        outline=True,
                                        size="sm",
                                        disabled=True,
                                    ),
                                    width="auto",
                                ),
                                dbc.Col(
                                    html.Div(id="hist-page-info", className="text-center text-muted small pt-1"),
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Next →",
                                        id="hist-next",
                                        color="secondary",
                                        outline=True,
                                        size="sm",
                                    ),
                                    width="auto",
                                    className="ms-auto",
                                ),
                            ],
                            className="mt-2 align-items-center",
                        ),
                    ],
                ),
                dbc.Tab(
                    label="Upcoming",
                    tab_id="upcoming",
                    children=[UPCOMING_CONTENT],
                ),
            ],
            id="tabs",
            active_tab="elo",
        ),

        # Refresh toast
        dbc.Toast(
            id="refresh-toast",
            header="Data Refresh",
            is_open=False,
            duration=4000,
            style={"position": "fixed", "top": 20, "right": 20, "zIndex": 9999},
        ),
    ],
    fluid=True,
)


# ── Callbacks ──────────────────────────────────────────────────────────────────

_H2H_FILTERS = [
    {"id": "h2h-filter-5",   "val": 5},
    {"id": "h2h-filter-10",  "val": 10},
    {"id": "h2h-filter-20",  "val": 20},
    {"id": "h2h-filter-all", "val": 0},
]


@app.callback(
    Output("h2h-filter-store", "data"),
    *[Output(f["id"], "color") for f in _H2H_FILTERS],
    *[Output(f["id"], "outline") for f in _H2H_FILTERS],
    *[Input(f["id"], "n_clicks") for f in _H2H_FILTERS],
    prevent_initial_call=True,
)
def update_h2h_filter(*_):
    triggered = ctx.triggered_id or "h2h-filter-10"
    val = next((f["val"] for f in _H2H_FILTERS if f["id"] == triggered), 10)
    colors = ["primary" if f["id"] == triggered else "secondary" for f in _H2H_FILTERS]
    outlines = [f["id"] != triggered for f in _H2H_FILTERS]
    return val, *colors, *outlines


@app.callback(
    Output("matchup-scoreboard", "children"),
    Output("matchup-chart", "figure"),
    Output("matchup-record", "children"),
    Output("matchup-h2h-table", "children"),
    Input("wp-visitor-store", "data"),
    Input("wp-home-store",    "data"),
    Input("h2h-filter-store", "data"),
)
def update_matchup(visitor, home, h2h_filter):
    if not visitor or not home or visitor == home:
        alert = dbc.Alert("Select two different teams.", color="warning")
        return alert, go.Figure(), None, None

    r_v = float(TEAMS[visitor][-1])
    r_h = float(TEAMS[home][-1])
    prob_v = NBARater.expectedResult(r_v, r_h)
    v_color = team_primary(visitor)
    h_color = team_primary(home)
    v_logo = logo_url(visitor)
    h_logo = logo_url(home)

    # H2H game log
    h2h_mask = (
        ((GAME_LOG["visitor"] == visitor) & (GAME_LOG["home"] == home))
        | ((GAME_LOG["visitor"] == home) & (GAME_LOG["home"] == visitor))
    )
    h2h_log = GAME_LOG[h2h_mask].sort_values("date").copy()

    if h2h_filter and h2h_filter > 0:
        h2h_filtered = h2h_log.tail(h2h_filter)
        record_label = f"Last {h2h_filter} Games"
    else:
        h2h_filtered = h2h_log
        record_label = "All-Time Record"

    a_wins = int(
        ((h2h_filtered["visitor"] == visitor) & (h2h_filtered["result"] == "visitor")).sum()
        + ((h2h_filtered["home"] == visitor) & (h2h_filtered["result"] == "home")).sum()
    )
    b_wins = len(h2h_filtered) - a_wins

    # Scoreboard card
    low_pct  = f"{max(0,   prob_v * 100 - 10):.1f}%"
    high_pct = f"{min(100, prob_v * 100 + 10):.1f}%"
    scoreboard = html.Div(
        style={
            "background": f"linear-gradient(90deg, {v_color}bb 0%, {v_color}33 {low_pct}, {h_color}33 {high_pct}, {h_color}bb 100%)",
            "border": "1px solid #e0e0e0",
            "borderRadius": "12px",
            "padding": "28px 24px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "marginBottom": "8px",
            "height": "100%",
        },
        children=[
            html.Div(
                [
                    html.Img(src=v_logo, style={"height": "80px", "marginBottom": "10px",
                                                 "filter": f"drop-shadow(0 0 8px {v_color}55)"}),
                    html.Div(f"{prob_v:.1%}", style={
                        "fontFamily": "Oswald, sans-serif", "fontSize": "2.6rem",
                        "fontWeight": "700", "color": v_color, "lineHeight": "1",
                    }),
                    html.Div(f"VISITOR · ELO {r_v:.0f}", style={
                        "fontSize": "0.65rem", "color": "#666",
                        "letterSpacing": "2px", "textTransform": "uppercase", "marginTop": "6px",
                    }),
                    html.Div(visitor, style={
                        "fontSize": "0.9rem", "fontWeight": "600", "color": "#222", "marginTop": "4px",
                    }),
                ],
                style={"textAlign": "center", "flex": "1"},
            ),
            html.Div(
                [
                    html.Div("VS", style={
                        "fontFamily": "Oswald, sans-serif", "fontSize": "1.6rem",
                        "fontWeight": "900", "color": "#ccc", "letterSpacing": "4px",
                    }),
                    html.Div(style={
                        "width": "1px", "height": "48px",
                        "background": "linear-gradient(to bottom, transparent, #ccc, transparent)",
                        "margin": "10px auto",
                    }),
                    html.Div("HOME COURT +100 ELO", style={
                        "fontSize": "0.55rem", "color": "#aaa",
                        "letterSpacing": "1px", "textTransform": "uppercase", "lineHeight": "1.6",
                    }),
                ],
                style={"textAlign": "center", "padding": "0 20px", "flexShrink": "0"},
            ),
            html.Div(
                [
                    html.Img(src=h_logo, style={"height": "80px", "marginBottom": "10px",
                                                 "filter": f"drop-shadow(0 0 8px {h_color}55)"}),
                    html.Div(f"{1 - prob_v:.1%}", style={
                        "fontFamily": "Oswald, sans-serif", "fontSize": "2.6rem",
                        "fontWeight": "700", "color": h_color, "lineHeight": "1",
                    }),
                    html.Div(f"HOME · ELO {r_h:.0f}", style={
                        "fontSize": "0.65rem", "color": "#666",
                        "letterSpacing": "2px", "textTransform": "uppercase", "marginTop": "6px",
                    }),
                    html.Div(home, style={
                        "fontSize": "0.9rem", "fontWeight": "600", "color": "#222", "marginTop": "4px",
                    }),
                ],
                style={"textAlign": "center", "flex": "1"},
            ),
        ],
    )

    # H2H ELO chart
    ts_v = TEAM_SERIES[TEAM_SERIES["team"] == visitor].sort_values("date")
    ts_h = TEAM_SERIES[TEAM_SERIES["team"] == home].sort_values("date")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts_v["date"], y=ts_v["elo"], mode="lines", name=visitor,
        line=dict(width=2, color=v_color),
    ))
    fig.add_trace(go.Scatter(
        x=ts_h["date"], y=ts_h["elo"], mode="lines", name=home,
        line=dict(width=2, color=h_color),
    ))

    if not h2h_filtered.empty:
        h2h_dates = pd.to_datetime(h2h_filtered["date"])
        v_elos = [
            row["visitor_after"] if row["visitor"] == visitor else row["home_after"]
            for _, row in h2h_filtered.iterrows()
        ]
        h_elos = [
            row["visitor_after"] if row["visitor"] == home else row["home_after"]
            for _, row in h2h_filtered.iterrows()
        ]
        fig.add_trace(go.Scatter(
            x=h2h_dates, y=v_elos, mode="markers",
            marker=dict(size=6, color=v_color, opacity=0.8),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=h2h_dates, y=h_elos, mode="markers",
            marker=dict(size=6, color=h_color, opacity=0.8),
            showlegend=False, hoverinfo="skip",
        ))

    xaxis_opts = dict(title="Date", rangeslider=dict(visible=True), type="date")
    if h2h_filter and h2h_filter > 0 and not h2h_filtered.empty:
        filtered_dates = pd.to_datetime(h2h_filtered["date"])
        pad = pd.Timedelta(days=30)
        xaxis_opts["range"] = [filtered_dates.min() - pad, filtered_dates.max() + pad]

    fig.update_layout(
        height=320,
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        xaxis=xaxis_opts,
        yaxis=dict(title="ELO Rating"),
        margin=dict(l=50, r=30, t=30, b=100),
    )

    # All-time record banner
    record_banner = html.Div(
        style={
            "background": f"linear-gradient(90deg, {v_color}11 0%, #f5f5f5 40%, #f5f5f5 60%, {h_color}11 100%)",
            "border": "1px solid #e0e0e0",
            "borderRadius": "12px",
            "padding": "20px 32px",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "space-between",
            "marginBottom": "16px",
        },
        children=[
            html.Div(
                [
                    html.Img(src=v_logo, style={"height": "60px",
                                                 "filter": f"drop-shadow(0 0 6px {v_color}55)"}),
                    html.Div(visitor, style={
                        "fontFamily": "Oswald, sans-serif", "fontSize": "0.9rem",
                        "color": "#555", "marginTop": "6px", "letterSpacing": "1px",
                    }),
                ],
                style={"textAlign": "center", "flex": "1"},
            ),
            html.Div(
                [
                    html.Div(f"{a_wins} – {b_wins}", style={
                        "fontFamily": "Oswald, sans-serif", "fontSize": "2.4rem",
                        "fontWeight": "700", "color": "#111", "letterSpacing": "4px",
                    }),
                    html.Div(record_label, style={
                        "fontSize": "0.6rem", "color": "#aaa",
                        "letterSpacing": "3px", "textTransform": "uppercase", "marginTop": "4px",
                    }),
                ],
                style={"textAlign": "center", "padding": "0 24px"},
            ),
            html.Div(
                [
                    html.Img(src=h_logo, style={"height": "60px",
                                                 "filter": f"drop-shadow(0 0 6px {h_color}55)"}),
                    html.Div(home, style={
                        "fontFamily": "Oswald, sans-serif", "fontSize": "0.9rem",
                        "color": "#555", "marginTop": "6px", "letterSpacing": "1px",
                    }),
                ],
                style={"textAlign": "center", "flex": "1"},
            ),
        ],
    )

    # H2H game log
    if h2h_filtered.empty:
        h2h_table = dbc.Alert("No games found between these two teams.", color="info")
    else:
        h2h_table = _game_log_table(h2h_filtered.sort_values("date", ascending=False))

    return scoreboard, fig, record_banner, h2h_table


app.clientside_callback(
    """
    function(eventJson, visitor, home) {
        if (!eventJson) return [visitor, home];
        try {
            var e = JSON.parse(eventJson);
            if (!e.slot || !e.team) return [visitor, home];
            if (e.slot === 'visitor') return [e.team, home];
            return [visitor, e.team];
        } catch(err) { return [visitor, home]; }
    }
    """,
    Output("wp-visitor-store", "data"),
    Output("wp-home-store",    "data"),
    Input("dnd-event", "value"),
    State("wp-visitor-store", "data"),
    State("wp-home-store",    "data"),
)


@app.callback(
    Output("drop-visitor", "children"),
    Output("drop-home",    "children"),
    Input("wp-visitor-store", "data"),
    Input("wp-home-store",    "data"),
)
def update_drop_zones(visitor, home):
    def slot_content(team):
        if not team:
            return html.Div("Drag a team here", className="text-muted small")
        return html.Div([
            html.Img(src=logo_url(team), style={"height": "48px"}),
            html.Div(team, style={"fontSize": "0.8rem", "marginTop": "4px"}),
        ], className="text-center")
    return slot_content(visitor), slot_content(home)


@app.callback(
    Output("hist-page", "data"),
    Input("hist-prev", "n_clicks"),
    Input("hist-next", "n_clicks"),
    Input("hist-team", "value"),
    Input("hist-season", "value"),
    State("hist-page", "data"),
    prevent_initial_call=True,
)
def update_hist_page(prev_clicks, next_clicks, team, season, current_page):
    triggered = ctx.triggered_id
    if triggered in ("hist-team", "hist-season"):
        return 0
    if triggered == "hist-prev":
        return max(0, (current_page or 0) - 1)
    if triggered == "hist-next":
        return (current_page or 0) + 1
    return current_page


@app.callback(
    Output("hist-table", "children"),
    Output("hist-page-info", "children"),
    Output("hist-prev", "disabled"),
    Output("hist-next", "disabled"),
    Input("hist-team", "value"),
    Input("hist-season", "value"),
    Input("hist-page", "data"),
)
def update_history(team, season, page):
    hist_log = GAME_LOG.sort_values("date", ascending=False).copy()
    if team and team != "All":
        hist_log = hist_log[(hist_log["visitor"] == team) | (hist_log["home"] == team)]
    if season and season != "All":
        hist_log = hist_log[hist_log["season"] == int(season)]
    hist_log = hist_log.reset_index(drop=True)

    total_pages = max(1, (len(hist_log) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(page or 0, total_pages - 1)
    page_data = hist_log.iloc[page * PAGE_SIZE: (page + 1) * PAGE_SIZE]

    table = _game_log_table(page_data)
    page_info = f"Page {page + 1} of {total_pages} · {len(hist_log):,} games"

    return table, page_info, page <= 0, page >= total_pages - 1


@app.callback(
    Output("refresh-toast", "children"),
    Output("refresh-toast", "is_open"),
    Input("refresh-btn", "n_clicks"),
    prevent_initial_call=True,
)
def refresh_data(n_clicks):
    try:
        today = date.today()
        season_start = today.year if today.month >= 10 else today.year - 1
        NBAScraper().data_years(beginning=season_start, end=season_start)
        return "Data updated. Refresh the page to see latest results.", True
    except Exception as exc:
        return f"Error: {exc}", True


@app.callback(
    Output("elo-chart", "figure"),
    *[Output(f"era-btn-{e['id']}", "color") for e in ERAS],
    *[Output(f"era-btn-{e['id']}", "outline") for e in ERAS],
    *[Input(f"era-btn-{e['id']}", "n_clicks") for e in ERAS],
)
def update_elo_era(*_):
    era_id = ctx.triggered_id.replace("era-btn-", "") if ctx.triggered_id else "all"
    fig = build_elo_figure(era_id)
    colors = ["primary" if e["id"] == era_id else "secondary" for e in ERAS]
    outlines = [False if e["id"] == era_id else True for e in ERAS]
    return fig, *colors, *outlines


if __name__ == "__main__":
    app.run(debug=True)
