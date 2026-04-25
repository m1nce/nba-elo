"""
Migrate SQLite data to PostgreSQL and pre-compute ELO history.

Run from the project root:
    uv run python -m backend.migrate
"""
import asyncio
import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import engine, Base
from backend.app.models import Game, EloHistory
from backend.NBARater import NBARater

SQLITE_PATH = Path("data") / "nba.db"
CHUNK = 1000


async def migrate(drop_first: bool = True) -> None:
    # (Re)create tables
    async with engine.begin() as conn:
        if drop_first:
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Read raw games from SQLite
    conn_sqlite = sqlite3.connect(str(SQLITE_PATH))
    df = pd.read_sql(
        "SELECT * FROM games "
        "WHERE visitor_points IS NOT NULL AND home_points IS NOT NULL "
        "ORDER BY date ASC",
        conn_sqlite,
    )
    conn_sqlite.close()

    # Prep for ELO simulation
    df["Win"] = (df["visitor_points"] > df["home_points"]).astype(float)
    df["Date"] = df["date"]
    df["Visitor"] = df["visitor"]
    df["Home"] = df["home"]
    df["Notes"] = df["notes"].fillna("")

    rater = NBARater()
    rater.eloSimulator(df)
    game_log = rater.getGameLog()

    # Build game records (merge scraped data with computed ELO columns)
    game_records = []
    for i, row in game_log.iterrows():
        orig = df.iloc[i]
        game_records.append({
            "date": row["date"],
            "season": int(row["season"]),
            "visitor": row["visitor"],
            "home": row["home"],
            "visitor_points": (
                int(orig["visitor_points"]) if pd.notna(orig["visitor_points"]) else None
            ),
            "home_points": (
                int(orig["home_points"]) if pd.notna(orig["home_points"]) else None
            ),
            "notes": str(row["notes"]) if pd.notna(row["notes"]) and row["notes"] else None,
            "result": row["result"],
            "visitor_elo_before": float(row["visitor_before"]),
            "visitor_elo_after": float(row["visitor_after"]),
            "home_elo_before": float(row["home_before"]),
            "home_elo_after": float(row["home_after"]),
            "visitor_delta": float(row["visitor_delta"]),
            "home_delta": float(row["home_delta"]),
            "win_prob_visitor": float(row["win_prob_visitor"]),
        })

    # Bulk insert games
    async with AsyncSession(engine) as session:
        for i in range(0, len(game_records), CHUNK):
            await session.execute(insert(Game), game_records[i : i + CHUNK])
        await session.commit()
    print(f"Inserted {len(game_records)} games")

    # Build ELO history records (one row per team per game)
    elo_records = []
    for _, row in game_log.iterrows():
        elo_records.append({"team": row["visitor"], "date": row["date"], "elo": float(row["visitor_after"])})
        elo_records.append({"team": row["home"],    "date": row["date"], "elo": float(row["home_after"])})

    async with AsyncSession(engine) as session:
        for i in range(0, len(elo_records), CHUNK):
            await session.execute(insert(EloHistory), elo_records[i : i + CHUNK])
        await session.commit()
    print(f"Inserted {len(elo_records)} ELO history entries")


async def migrate_season(season: int) -> None:
    """Re-compute and replace a single season's data in Postgres.

    Runs the full ELO simulation (history is sequential) but only deletes and
    re-inserts records for the given season, leaving prior seasons untouched.
    """
    from sqlalchemy import delete as sa_delete

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    conn_sqlite = sqlite3.connect(str(SQLITE_PATH))
    df = pd.read_sql(
        "SELECT * FROM games "
        "WHERE visitor_points IS NOT NULL AND home_points IS NOT NULL "
        "ORDER BY date ASC",
        conn_sqlite,
    )
    conn_sqlite.close()

    df["Win"] = (df["visitor_points"] > df["home_points"]).astype(float)
    df["Date"] = df["date"]
    df["Visitor"] = df["visitor"]
    df["Home"] = df["home"]
    df["Notes"] = df["notes"].fillna("")

    rater = NBARater()
    rater.eloSimulator(df)
    game_log = rater.getGameLog()

    season_mask = game_log["season"] == season
    season_log = game_log[season_mask]
    season_indices = season_log.index.tolist()

    game_records = []
    for i in season_indices:
        row = game_log.iloc[i]
        orig = df.iloc[i]
        game_records.append({
            "date": row["date"],
            "season": int(row["season"]),
            "visitor": row["visitor"],
            "home": row["home"],
            "visitor_points": int(orig["visitor_points"]) if pd.notna(orig["visitor_points"]) else None,
            "home_points": int(orig["home_points"]) if pd.notna(orig["home_points"]) else None,
            "notes": str(row["notes"]) if pd.notna(row["notes"]) and row["notes"] else None,
            "result": row["result"],
            "visitor_elo_before": float(row["visitor_before"]),
            "visitor_elo_after": float(row["visitor_after"]),
            "home_elo_before": float(row["home_before"]),
            "home_elo_after": float(row["home_after"]),
            "visitor_delta": float(row["visitor_delta"]),
            "home_delta": float(row["home_delta"]),
            "win_prob_visitor": float(row["win_prob_visitor"]),
        })

    elo_records = []
    for _, row in season_log.iterrows():
        elo_records.append({"team": row["visitor"], "date": row["date"], "elo": float(row["visitor_after"])})
        elo_records.append({"team": row["home"],    "date": row["date"], "elo": float(row["home_after"])})

    # Season date bounds: Oct 1 of season year → Sep 30 of next year
    season_start = f"{season}-10-01"
    season_end = f"{season + 1}-09-30"

    async with AsyncSession(engine) as session:
        await session.execute(sa_delete(Game).where(Game.season == season))
        await session.execute(
            sa_delete(EloHistory).where(
                EloHistory.date >= season_start,
                EloHistory.date <= season_end,
            )
        )
        await session.commit()

    async with AsyncSession(engine) as session:
        for i in range(0, len(game_records), CHUNK):
            await session.execute(insert(Game), game_records[i : i + CHUNK])
        for i in range(0, len(elo_records), CHUNK):
            await session.execute(insert(EloHistory), elo_records[i : i + CHUNK])
        await session.commit()

    print(f"Season {season}: replaced {len(game_records)} games, {len(elo_records)} ELO entries")


if __name__ == "__main__":
    asyncio.run(migrate())
