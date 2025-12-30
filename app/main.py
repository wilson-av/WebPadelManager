from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routers import (
    home_router,
    competition_router,
    game_day_router,
    player_router,
    match_router
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Montar a pasta static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(home_router.router)
app.include_router(competition_router.router)
app.include_router(game_day_router.router)
app.include_router(match_router.router)
#app.include_router(game_day_router.router, prefix="/game-days")
app.include_router(player_router.router)
