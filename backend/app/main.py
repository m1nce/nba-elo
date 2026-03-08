import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import elo, standings, matchup, games, upcoming, refresh, meta
from .routers.upcoming import refresh_upcoming_db, _is_stale


async def _startup_refresh():
    if await _is_stale():
        await refresh_upcoming_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(_startup_refresh())  # fire-and-forget, non-blocking
    yield


app = FastAPI(title="NBA ELO API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(elo.router,        prefix="/api")
app.include_router(standings.router,  prefix="/api")
app.include_router(matchup.router,    prefix="/api")
app.include_router(games.router,      prefix="/api")
app.include_router(upcoming.router,   prefix="/api")
app.include_router(refresh.router,    prefix="/api")
app.include_router(meta.router,       prefix="/api")
