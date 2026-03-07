from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from ..database import get_db
from ..models import Game
from ..schemas import StandingRow
from ..team_meta import TEAM_META, logo_url, get_current_season

router = APIRouter()


@router.get("/standings", response_model=list[StandingRow])
async def get_standings(db: AsyncSession = Depends(get_db)):
    current_season = get_current_season()

    # Latest ELO per team via PostgreSQL DISTINCT ON
    elo_result = await db.execute(
        text("""
            SELECT DISTINCT ON (team) team, elo
            FROM elo_history
            ORDER BY team, date DESC
        """)
    )
    current_elos: dict[str, float] = {row.team: row.elo for row in elo_result}

    # Season-start ELO: elo_before on each team's first game this season
    games_result = await db.execute(
        select(Game)
        .where(Game.season == current_season, Game.visitor_elo_before.isnot(None))
        .order_by(Game.date)
    )
    season_games = games_result.scalars().all()

    start_elos: dict[str, float] = {}
    for g in season_games:
        if g.visitor not in start_elos and g.visitor_elo_before is not None:
            start_elos[g.visitor] = g.visitor_elo_before
        if g.home not in start_elos and g.home_elo_before is not None:
            start_elos[g.home] = g.home_elo_before

    rows: list[StandingRow] = []
    for rank, (team, current_elo) in enumerate(
        sorted(current_elos.items(), key=lambda x: -x[1]), 1
    ):
        if team not in TEAM_META:
            continue
        start_elo = start_elos.get(team, current_elo)
        rows.append(
            StandingRow(
                rank=rank,
                team=team,
                logo_url=logo_url(team),
                current_elo=round(current_elo, 1),
                delta=round(current_elo - start_elo, 1),
            )
        )

    return rows
