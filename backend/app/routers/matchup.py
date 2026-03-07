from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, text

from ..database import get_db
from ..models import Game, EloHistory
from ..schemas import MatchupResponse, GameRow, EloDataPoint
from ..team_meta import TEAM_META, logo_url, team_primary
from backend.NBARater import NBARater

router = APIRouter()


def _game_to_row(g: Game) -> GameRow:
    return GameRow(
        id=g.id,
        date=g.date,
        season=g.season,
        visitor=g.visitor,
        home=g.home,
        visitor_points=g.visitor_points,
        home_points=g.home_points,
        result=g.result,
        visitor_elo_before=g.visitor_elo_before,
        visitor_elo_after=g.visitor_elo_after,
        home_elo_before=g.home_elo_before,
        home_elo_after=g.home_elo_after,
        visitor_delta=g.visitor_delta,
        home_delta=g.home_delta,
        win_prob_visitor=g.win_prob_visitor,
        notes=g.notes,
    )


@router.get("/matchup", response_model=MatchupResponse)
async def get_matchup(
    visitor: str = Query(...),
    home: str = Query(...),
    h2h_filter: int = Query(10),
    db: AsyncSession = Depends(get_db),
):
    if visitor == home:
        raise HTTPException(status_code=400, detail="Visitor and home must be different teams.")
    if visitor not in TEAM_META or home not in TEAM_META:
        raise HTTPException(status_code=404, detail="Unknown team name.")

    # Current ELO for both teams
    elo_result = await db.execute(
        text("""
            SELECT DISTINCT ON (team) team, elo
            FROM elo_history
            WHERE team IN (:v, :h)
            ORDER BY team, date DESC
        """),
        {"v": visitor, "h": home},
    )
    elos = {row.team: row.elo for row in elo_result}
    r_v = elos.get(visitor, 1200.0)
    r_h = elos.get(home, 1200.0)
    prob_v = NBARater.expectedResult(r_v, r_h)

    # H2H game log (all time, ascending)
    h2h_result = await db.execute(
        select(Game)
        .where(
            or_(
                and_(Game.visitor == visitor, Game.home == home),
                and_(Game.visitor == home, Game.home == visitor),
            )
        )
        .order_by(Game.date)
    )
    h2h_all = h2h_result.scalars().all()

    if h2h_filter > 0:
        h2h = h2h_all[-h2h_filter:]
        record_label = f"Last {h2h_filter} Games"
    else:
        h2h = h2h_all
        record_label = "All-Time Record"

    a_wins = sum(
        1 for g in h2h
        if (g.visitor == visitor and g.result == "visitor")
        or (g.home == visitor and g.result == "home")
    )
    b_wins = len(h2h) - a_wins

    # Full ELO history for chart
    elo_hist_result = await db.execute(
        select(EloHistory)
        .where(EloHistory.team.in_([visitor, home]))
        .order_by(EloHistory.team, EloHistory.date)
    )
    elo_hist_rows = elo_hist_result.scalars().all()
    elo_v = [EloDataPoint(date=r.date, elo=r.elo) for r in elo_hist_rows if r.team == visitor]
    elo_h = [EloDataPoint(date=r.date, elo=r.elo) for r in elo_hist_rows if r.team == home]

    return MatchupResponse(
        visitor=visitor,
        home=home,
        prob_v=prob_v,
        prob_h=1 - prob_v,
        r_v=r_v,
        r_h=r_h,
        v_color=team_primary(visitor),
        h_color=team_primary(home),
        v_logo=logo_url(visitor),
        h_logo=logo_url(home),
        a_wins=a_wins,
        b_wins=b_wins,
        record_label=record_label,
        elo_history_v=elo_v,
        elo_history_h=elo_h,
        h2h_games=[_game_to_row(g) for g in reversed(h2h)],
    )
