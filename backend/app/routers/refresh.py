import asyncio
from datetime import date
from fastapi import APIRouter, BackgroundTasks

router = APIRouter()
_refresh_running = False


async def _run_refresh():
    global _refresh_running
    _refresh_running = True
    try:
        from backend.NBAScraper import NBAScraper
        from backend.migrate import migrate

        today = date.today()
        season = today.year if today.month >= 10 else today.year - 1

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: NBAScraper().data_years(beginning=season, end=season),
        )
        await migrate(drop_first=False)
    finally:
        _refresh_running = False
        # Invalidate upcoming cache
        import backend.app.routers.upcoming as up_router
        up_router._cache_data = None
        up_router._cache_time = 0.0


@router.post("/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    if _refresh_running:
        return {"message": "Refresh already in progress."}
    background_tasks.add_task(_run_refresh)
    return {"message": "Data refresh started in background."}
