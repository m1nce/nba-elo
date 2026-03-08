from math import ceil
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from ..database import get_db
from ..models import Game
from ..schemas import GameRow, PaginatedGames
from ..team_meta import logo_url

router = APIRouter()


def _game_to_row(g: Game) -> GameRow:
    return GameRow(
        id=g.id,
        date=g.date,
        season=g.season,
        visitor=g.visitor,
        home=g.home,
        v_logo=logo_url(g.visitor),
        h_logo=logo_url(g.home),
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


@router.get("/games", response_model=PaginatedGames)
async def get_games(
    team: str = Query("All"),
    season: str = Query("All"),
    page: int = Query(0, ge=0),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Game).where(Game.visitor_points.isnot(None))

    if team != "All":
        base_query = base_query.where(or_(Game.visitor == team, Game.home == team))
    if season != "All":
        base_query = base_query.where(Game.season == int(season))

    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar() or 0

    data_result = await db.execute(
        base_query.order_by(Game.date.desc())
        .offset(page * page_size)
        .limit(page_size)
    )
    games = data_result.scalars().all()

    return PaginatedGames(
        games=[_game_to_row(g) for g in games],
        total=total,
        page=page,
        total_pages=max(1, ceil(total / page_size)),
    )
