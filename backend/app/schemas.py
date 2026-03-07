from pydantic import BaseModel
from typing import Optional


class EloDataPoint(BaseModel):
    date: str
    elo: float


class TeamEloSeries(BaseModel):
    team: str
    color: str
    data: list[EloDataPoint]


class StandingRow(BaseModel):
    rank: int
    team: str
    logo_url: str
    current_elo: float
    delta: float


class GameRow(BaseModel):
    id: int
    date: str
    season: int
    visitor: str
    home: str
    visitor_points: Optional[int] = None
    home_points: Optional[int] = None
    result: Optional[str] = None
    visitor_elo_before: Optional[float] = None
    visitor_elo_after: Optional[float] = None
    home_elo_before: Optional[float] = None
    home_elo_after: Optional[float] = None
    visitor_delta: Optional[float] = None
    home_delta: Optional[float] = None
    win_prob_visitor: Optional[float] = None
    notes: Optional[str] = None


class PaginatedGames(BaseModel):
    games: list[GameRow]
    total: int
    page: int
    total_pages: int


class MatchupResponse(BaseModel):
    visitor: str
    home: str
    prob_v: float
    prob_h: float
    r_v: float
    r_h: float
    v_color: str
    h_color: str
    v_logo: str
    h_logo: str
    a_wins: int
    b_wins: int
    record_label: str
    elo_history_v: list[EloDataPoint]
    elo_history_h: list[EloDataPoint]
    h2h_games: list[GameRow]


class UpcomingGame(BaseModel):
    date: str
    visitor: str
    home: str
    v_logo: str
    h_logo: str
    prob_v: float
    prob_h: float
    r_v: float
    r_h: float


class TeamMeta(BaseModel):
    name: str
    abbrev: str
    primary: str
    secondary: str
    logo_url: str


class EraInfo(BaseModel):
    id: str
    label: str
