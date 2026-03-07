import asyncio
import time
from fastapi import APIRouter
from sqlalchemy import text

from ..schemas import UpcomingGame
from ..team_meta import logo_url, TEAM_META
from backend.NBARater import NBARater
from backend.NBAScraper import NBAScraper

router = APIRouter()

_cache_data: list[UpcomingGame] | None = None
_cache_time: float = 0.0
_CACHE_TTL = 3600.0  # 1 hour


async def _get_current_elos() -> dict[str, float]:
    from ..database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT DISTINCT ON (team) team, elo
                FROM elo_history
                ORDER BY team, date DESC
            """)
        )
        return {row.team: row.elo for row in result}


def _map(name: str) -> str:
    return NBARater.map_team_names(name)


@router.get("/upcoming", response_model=list[UpcomingGame])
async def get_upcoming():
    global _cache_data, _cache_time

    if _cache_data is not None and (time.time() - _cache_time) < _CACHE_TTL:
        return _cache_data

    loop = asyncio.get_event_loop()
    scraper = NBAScraper()
    df = await loop.run_in_executor(None, lambda: scraper.scrape_upcoming(days=7))

    current_elos = await _get_current_elos()

    def get_elo(raw_name: str) -> float:
        return current_elos.get(_map(raw_name), 1200.0)

    games: list[UpcomingGame] = []
    for _, row in df.iterrows():
        v_name = _map(row["visitor"])
        h_name = _map(row["home"])
        r_v = get_elo(row["visitor"])
        r_h = get_elo(row["home"])
        prob_v = NBARater.expectedResult(r_v, r_h)
        games.append(
            UpcomingGame(
                date=row["date"],
                visitor=row["visitor"],
                home=row["home"],
                v_logo=logo_url(v_name),
                h_logo=logo_url(h_name),
                prob_v=prob_v,
                prob_h=1 - prob_v,
                r_v=r_v,
                r_h=r_h,
            )
        )

    _cache_data = games
    _cache_time = time.time()
    return games
