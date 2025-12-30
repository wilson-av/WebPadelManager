from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.competition_service import get_all, create
from fastapi.templating import Jinja2Templates
from app.services.game_day_service import get_by_competition
from app.models.competition import Competition
from app.models.player import Player
from app.models.game_day import GameDay
from app.models.match import Match 
from sqlalchemy import func
from datetime import datetime


router = APIRouter(prefix="/competitions")
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def list_competitions(request: Request, db: Session = Depends(get_db), search: str = Query(None)):
    competitions = get_all(db)
    competitions_data = []

    for c in competitions:
        if search and search.lower() not in c.name.lower():
            continue
        # Total de dias de jogo
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
        "competitions.html",
        {"request": request, "competitions": competitions_data, "search": search or ""}
    )

# Criar novo torneio
@router.get("/new", response_class=HTMLResponse)
def new_competition(request: Request):
    return templates.TemplateResponse(
        "competition_create.html",
        {"request": request}
    )

@router.post("/new")
def create_competition(
    name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    db: Session = Depends(get_db)
):
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    create(db, name, start_date_obj, end_date_obj)
    return RedirectResponse("/competitions", status_code=303)

@router.get("/edit/{competition_id}", response_class=HTMLResponse)
def edit_competition(request: Request, competition_id: str, db: Session = Depends(get_db)):
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    return templates.TemplateResponse(
        "competition_edit.html",
        {"request": request, "competition": competition}
    )

@router.post("/edit/{competition_id}")
def update_competition(
    competition_id: str,
    name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if competition:
        competition.name = name
        competition.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        competition.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        competition.status = status
        db.commit()
        db.refresh(competition)
    return RedirectResponse("/competitions", status_code=303)

@router.get("/{competition_id}/ranking", response_class=HTMLResponse)
def competition_ranking(
    request: Request,
    competition_id: str,
    db: Session = Depends(get_db)
):
    competition = db.query(Competition).filter(
        Competition.id == competition_id
    ).first()

    if not competition:
        raise HTTPException(404, "Competition not found")

    matches = (
        db.query(Match)
        .join(GameDay)
        .filter(GameDay.competition_id == competition_id)
        .all()
    )

    ranking = {}

    def init_player(player: Player):
        if player.id not in ranking:
            ranking[player.id] = {
                "name": player.name,
                "games": 0,
                "wins": 0,
                "ties": 0,
                "losses": 0,
                "points_for": 0,
                "points_against": 0,
            }

    for match in matches:
        a_pts = match.points_team_a
        b_pts = match.points_team_b

        # Resultado
        if a_pts > b_pts:
            result_a, result_b = "W", "L"
        elif a_pts < b_pts:
            result_a, result_b = "L", "W"
        else:
            result_a = result_b = "T"

        # IDs das equipas
        team_a_ids = match.team_a_players.split(",")
        team_b_ids = match.team_b_players.split(",")

        team_a_players = db.query(Player).filter(Player.id.in_(team_a_ids)).all()
        team_b_players = db.query(Player).filter(Player.id.in_(team_b_ids)).all()

        # Equipa A
        for player in team_a_players:
            init_player(player)
            p = ranking[player.id]

            p["games"] += 1
            p["points_for"] += a_pts
            p["points_against"] += b_pts

            if result_a == "W":
                p["wins"] += 1
            elif result_a == "T":
                p["ties"] += 1
            else:
                p["losses"] += 1

        # Equipa B
        for player in team_b_players:
            init_player(player)
            p = ranking[player.id]

            p["games"] += 1
            p["points_for"] += b_pts
            p["points_against"] += a_pts

            if result_b == "W":
                p["wins"] += 1
            elif result_b == "T":
                p["ties"] += 1
            else:
                p["losses"] += 1

    # Lista final
    ranking_list = []
    for r in ranking.values():
        games = r["games"]
        win_rate = (r["wins"] / games * 100) if games > 0 else 0

        ranking_list.append({
            **r,
            "points": r["points_for"],
            "win_rate": round(win_rate, 1),
        })

    ranking_list.sort(
        key=lambda x: (x["points"], x["win_rate"]),
        reverse=True
    )

    return templates.TemplateResponse(
        "competition_ranking.html",
        {
            "request": request,
            "competition": competition,
            "ranking": ranking_list
        }
    )
