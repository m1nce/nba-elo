from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import EloHistory
from ..schemas import TeamEloSeries, EloDataPoint
from ..team_meta import TEAM_META, team_primary, get_current_season, get_era_date_range

router = APIRouter()


@router.get("/elo/history", response_model=list[TeamEloSeries])
async def get_elo_history(
    era: str = Query("all"),
    db: AsyncSession = Depends(get_db),
):
    current_season = get_current_season()
    start_date, end_date = get_era_date_range(era, current_season)

    result = await db.execute(
        select(EloHistory)
        .where(EloHistory.date >= start_date, EloHistory.date <= end_date)
        .order_by(EloHistory.team, EloHistory.date)
    )
    rows = result.scalars().all()

    teams: dict[str, list[EloDataPoint]] = {}
    for row in rows:
        if row.team not in teams:
            teams[row.team] = []
        teams[row.team].append(EloDataPoint(date=row.date, elo=row.elo))

    return [
        TeamEloSeries(team=team, color=team_primary(team), data=data_points)
        for team, data_points in teams.items()
        if team in TEAM_META
    ]
