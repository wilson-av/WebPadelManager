from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from app.database import get_db
from app.services.competition_service import get_all
from app.services.game_day_service import get_by_competition

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db), search: str = Query(None)):
    competitions = get_all(db)
    competitions_data = []

    for c in competitions:
        if search and search.lower() not in c.name.lower():
            continue
        total_days = len(get_by_competition(db, c.id))
        competitions_data.append({
            "id": c.id,
            "name": c.name,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "total_days": total_days,
            "status": c.status  
        })

    return templates.TemplateResponse(
        "competitions.html",  # usamos o mesmo template da lista de competições
        {"request": request, "competitions": competitions_data, "search": search or ""}
    )
