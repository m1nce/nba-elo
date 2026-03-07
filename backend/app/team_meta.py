from datetime import date

TEAM_META: dict[str, dict[str, str]] = {
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
    {"id": "bird",   "label": "Bird / Magic 79-91", "start": 1979, "end": 1991},
    {"id": "jordan", "label": "Jordan 91-98",        "start": 1991, "end": 1998},
    {"id": "kobe",   "label": "Kobe Era 96-16",      "start": 1996, "end": 2016},
    {"id": "lebron", "label": "LeBron 03-now",        "start": 2003, "end": 9999},
    {"id": "last5",   "label": "Last 5 Yrs",           "start": -5,   "end": 9999},
    {"id": "current", "label": "Current Season",       "start": -1,   "end": 9999},
]


def get_current_season() -> int:
    today = date.today()
    return today.year if today.month >= 10 else today.year - 1


def logo_url(team_name: str) -> str:
    abbrev = TEAM_META.get(team_name, {}).get("abbrev", "")
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{abbrev}.png" if abbrev else ""


def team_primary(team_name: str) -> str:
    return TEAM_META.get(team_name, {}).get("primary", "#333333")


def get_era_date_range(era_id: str, current_season: int) -> tuple[str, str]:
    era = next((e for e in ERAS if e["id"] == era_id), ERAS[0])
    if era["start"] == -1:
        return f"{current_season}-10-01", date.today().isoformat()
    start_year = current_season - 4 if era["start"] == -5 else era["start"]
    end_date = date.today().isoformat() if era["end"] == 9999 else f"{era['end']}-12-31"
    return f"{start_year}-01-01", end_date
