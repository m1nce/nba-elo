from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import Game
from ..schemas import TeamMeta, EraInfo
from ..team_meta import TEAM_META, ERAS, logo_url

router = APIRouter()


@router.get("/teams", response_model=list[TeamMeta])
async def get_teams():
    return [
        TeamMeta(
            name=name,
            abbrev=meta["abbrev"],
            primary=meta["primary"],
            secondary=meta["secondary"],
            logo_url=logo_url(name),
        )
        for name, meta in sorted(TEAM_META.items())
    ]


@router.get("/seasons", response_model=list[int])
async def get_seasons(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game.season).distinct().order_by(Game.season.desc())
    )
    return [row[0] for row in result]


@router.get("/eras", response_model=list[EraInfo])
async def get_eras():
    return [EraInfo(id=e["id"], label=e["label"]) for e in ERAS]
