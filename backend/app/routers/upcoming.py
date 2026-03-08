import asyncio
from datetime import datetime, timezone, date as date_type
from fastapi import APIRouter
from sqlalchemy import text, delete

from ..database import AsyncSessionLocal
from ..models import UpcomingGameDB
from ..schemas import UpcomingGame
from ..team_meta import logo_url
from backend.NBARater import NBARater
from backend.NBAScraper import NBAScraper

router = APIRouter()


async def _get_current_elos() -> dict[str, float]:
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


async def _is_stale() -> bool:
    today = date_type.today().isoformat()
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(text("SELECT COUNT(*) FROM upcoming_games"))
        if count_result.scalar() == 0:
            return True
        fresh_result = await session.execute(
            text("SELECT scraped_at FROM upcoming_games LIMIT 1")
        )
        row = fresh_result.fetchone()
        if row is None:
            return True
        scraped_date = row.scraped_at.date().isoformat()
        if scraped_date < today:
            return True
        future_result = await session.execute(
            text("SELECT COUNT(*) FROM upcoming_games WHERE date >= :today"),
            {"today": today},
        )
        if future_result.scalar() == 0:
            return True
    return False


async def _read_from_db() -> list[UpcomingGame]:
    today = date_type.today().isoformat()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM upcoming_games WHERE date >= :today ORDER BY date"),
            {"today": today},
        )
        rows = result.fetchall()
    return [
        UpcomingGame(
            date=r.date,
            visitor=r.visitor,
            home=r.home,
            v_logo=r.v_logo,
            h_logo=r.h_logo,
            prob_v=r.prob_v,
            prob_h=r.prob_h,
            r_v=r.r_v,
            r_h=r.r_h,
        )
        for r in rows
    ]


async def refresh_upcoming_db() -> list[UpcomingGame]:
    loop = asyncio.get_event_loop()
    scraper = NBAScraper()
    df = await loop.run_in_executor(None, lambda: scraper.scrape_upcoming(days=7))

    current_elos = await _get_current_elos()

    def get_elo(raw_name: str) -> float:
        return current_elos.get(_map(raw_name), 1200.0)

    now = datetime.now(timezone.utc)
    games: list[UpcomingGame] = []
    db_rows: list[UpcomingGameDB] = []

    for _, row in df.iterrows():
        v_name = _map(row["visitor"])
        h_name = _map(row["home"])
        r_v = get_elo(row["visitor"])
        r_h = get_elo(row["home"])
        prob_v = NBARater.expectedResult(r_v, r_h)

        game = UpcomingGame(
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
        games.append(game)
        db_rows.append(
            UpcomingGameDB(
                date=game.date,
                visitor=game.visitor,
                home=game.home,
                v_logo=game.v_logo,
                h_logo=game.h_logo,
                prob_v=game.prob_v,
                prob_h=game.prob_h,
                r_v=game.r_v,
                r_h=game.r_h,
                scraped_at=now,
            )
        )

    async with AsyncSessionLocal() as session:
        await session.execute(delete(UpcomingGameDB))
        session.add_all(db_rows)
        await session.commit()

    return games


@router.get("/upcoming", response_model=list[UpcomingGame])
async def get_upcoming():
    if await _is_stale():
        return await refresh_upcoming_db()
    return await _read_from_db()
