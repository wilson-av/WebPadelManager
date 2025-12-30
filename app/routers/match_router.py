from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
#from app.services.match_service import get_by_game_day
from fastapi.templating import Jinja2Templates
from app.models.match import Match
from app.models.game_day import GameDay
from app.models.player import Player
from app.services.competition_service import get_by_id

from fastapi.responses import StreamingResponse
import io


router = APIRouter(prefix="/matches")
templates = Jinja2Templates(directory="app/templates")

@router.post("/update-score/{match_id}")
def update_score(
    match_id: str,
    points_team_a: int = Form(...),
    points_team_b: int = Form(...),
    db: Session = Depends(get_db)
):
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(404, "Match not found")

    match.points_team_a = points_team_a
    match.points_team_b = points_team_b
    db.commit()

    return RedirectResponse(
        url=f"/matches/{match.game_day_id}/matches",
        status_code=303
    )

@router.post("/save-all/{game_day_id}")
async def save_all_scores(
    game_day_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()

    matches = db.query(Match).filter(
        Match.game_day_id == game_day_id
    ).all()

    for match in matches:
        a_key = f"points_team_a_{match.id}"
        b_key = f"points_team_b_{match.id}"

        if a_key in form and b_key in form:
            match.points_team_a = int(form[a_key])
            match.points_team_b = int(form[b_key])

    db.commit()

    return RedirectResponse(
        url=f"/matches/{game_day_id}/matches",
        status_code=303
    )


@router.get("/{game_day_id}/matches")
def view_matches(game_day_id: str, request: Request, db: Session = Depends(get_db)):
    game_day = db.query(GameDay).filter(GameDay.id == game_day_id).first()
    if not game_day:
        raise HTTPException(404, "Game day not found")

    competition = get_by_id(db, game_day.competition_id)

    matches = db.query(Match).filter(Match.game_day_id == game_day_id).order_by(Match.order, Match.court).all()
    all_players = db.query(Player).all()
    all_players_dict = {p.id: p for p in all_players}

    total_games = len(matches)
    total_points = sum(
        m.points_team_a + m.points_team_b for m in matches
    )
    rounds = len(set(m.order for m in matches))
    
    summary = {
        "games": total_games,
        "rounds": rounds,
        "points": total_points,
        "avg_points": round(total_points / total_games, 1) if total_games else 0
    }

# ---------- CALCULAR TOP 3 DO GAME DAY ----------
    ranking = {}
    for match in matches:
        for pid, pts in [(match.team_a_players.split(','), match.points_team_a),
                         (match.team_b_players.split(','), match.points_team_b)]:
            for player_id in pid:
                if player_id not in ranking:
                    ranking[player_id] = {"name": all_players_dict[player_id].name, "points": 0}
                ranking[player_id]["points"] += pts

    top3 = sorted(ranking.values(), key=lambda x: x["points"], reverse=True)[:3]
    

    return templates.TemplateResponse(
        "matches.html",
        {
            "request": request,
            "game_day": game_day,
            "competition": competition,
            "matches": matches,
            "all_players_dict": all_players_dict,
            "summary": summary,
            "top3": top3  # <-- enviar para o template
        }
    )