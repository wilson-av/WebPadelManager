from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.game_day_service import (
    get_by_competition, create, add_player, remove_player, replace_player
)
from app.services.competition_service import get_by_id as get_competition
from app.models.player import Player
from fastapi.templating import Jinja2Templates
from app.services.game_day_service import get_by_id
from datetime import datetime
from app.models.competition import Competition
from app.models.game_day import GameDay
from app.models.match import Match
import uuid
import random
from collections import defaultdict


router = APIRouter(prefix="/game-days")
templates = Jinja2Templates(directory="app/templates")

@router.post("/delete/{day_id}")
def delete_game_day(day_id: str, db: Session = Depends(get_db)):
    day = db.query(GameDay).filter(GameDay.id == day_id).first()

    if not day:
        raise HTTPException(status_code=404, detail="Game Day não encontrado")

    # Verificar se existem jogos
    has_matches = db.query(Match).filter(
        Match.game_day_id == day_id
    ).count() > 0

    if has_matches or len(day.players) > 0:
        raise HTTPException(
            status_code=400,
            detail="Não é possível eliminar um dia com jogos ou jogadores inscritos"
        )

    db.delete(day)
    db.commit()

    return RedirectResponse(
        url=f"/game-days/competition/{day.competition_id}",
        status_code=303
    )

@router.get("/{game_day_id}/ranking", response_class=HTMLResponse)
def game_day_ranking(
    game_day_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    game_day = db.query(GameDay).filter(GameDay.id == game_day_id).first()
    if not game_day:
        raise HTTPException(404, "Game day not found")

    competition = db.query(Competition).filter(
        Competition.id == game_day.competition_id
    ).first()

    matches = db.query(Match).filter(
        Match.game_day_id == game_day_id
    ).all()

    ranking = defaultdict(lambda: {
        "games": 0,
        "wins": 0,
        "ties": 0,
        "losses": 0,
        "points_for": 0,
        "points_against": 0,
    })

    players = {p.id: p for p in db.query(Player).all()}

    for match in matches:
        a_pts = match.points_team_a
        b_pts = match.points_team_b

        if a_pts > b_pts:
            res_a, res_b = "W", "L"
        elif a_pts < b_pts:
            res_a, res_b = "L", "W"
        else:
            res_a = res_b = "T"

        team_a = match.team_a_players.split(",")
        team_b = match.team_b_players.split(",")

        for pid in team_a:
            r = ranking[pid]
            r["games"] += 1
            r["points_for"] += a_pts
            r["points_against"] += b_pts
            if res_a == "W": r["wins"] += 1
            elif res_a == "T": r["ties"] += 1
            else: r["losses"] += 1

        for pid in team_b:
            r = ranking[pid]
            r["games"] += 1
            r["points_for"] += b_pts
            r["points_against"] += a_pts
            if res_b == "W": r["wins"] += 1
            elif res_b == "T": r["ties"] += 1
            else: r["losses"] += 1

    ranking_list = []
    for pid, r in ranking.items():
        games = r["games"]
        win_rate = (r["wins"] / games * 100) if games else 0

        ranking_list.append({
            "name": players[pid].name,
            "games": games,
            "record": f"{r['wins']} - {r['ties']} - {r['losses']}",
            "win_rate": round(win_rate, 1),
            "points": r["points_for"],
            "points_against": r["points_against"]
        })

    ranking_list.sort(key=lambda x: (x["points"], x["win_rate"]), reverse=True)

    return templates.TemplateResponse(
        "game_day_ranking.html",
        {
            "request": request,
            "competition": competition,
            "game_day": game_day,
            "ranking": ranking_list
        }
    )

# Listagem de dias com inscrições
@router.get("/competition/{competition_id}", response_class=HTMLResponse)
def list_game_days(
    request: Request,
    competition_id: str,
    db: Session = Depends(get_db)
):
    competition = db.query(Competition).filter(
        Competition.id == competition_id
    ).first()

    game_days = db.query(GameDay).filter(
        GameDay.competition_id == competition_id
    ).order_by(GameDay.date).all()

    all_players = db.query(Player).order_by(Player.name).all()

    game_days_data = []
    for day in game_days:
        max_players = day.num_courts * 4
        current_players = len(day.players)

        matches_count = db.query(Match).filter(Match.game_day_id == day.id).count()

        game_days_data.append({
            "id": day.id,
            "date": day.date,
            "num_courts": day.num_courts,
            "group_name": day.group_name,
            "players": day.players,
            "current_players": current_players,
            "max_players": max_players,
            "has_matches": matches_count > 0   # 👈 chave importante
        })

    return templates.TemplateResponse(
        "game_days.html",
        {
            "request": request,
            "competition": competition,
            "game_days": game_days_data,
            "all_players": all_players
        }
    )

# Form para criar dia de jogo com número de campos
@router.get("/new/{competition_id}", response_class=HTMLResponse)
def new_game_day(request: Request, competition_id: str, db: Session = Depends(get_db)):
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    return templates.TemplateResponse(
        "game_day_create.html",
        {"request": request, "competition": competition}
    )

@router.post("/new/{competition_id}")
def create_game_day(
    competition_id: str,
    date: str = Form(...),
    num_courts: int = Form(...),
    group_name: str = Form(...),
    db: Session = Depends(get_db)
):
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if competition:
        gd = GameDay(
            id=str(uuid.uuid4()),
            competition_id=competition.id,
            date=datetime.strptime(date, "%Y-%m-%d").date(),
            num_courts=max(2, num_courts),
            group_name=group_name
        )
        db.add(gd)
        db.commit()
    return RedirectResponse(f"/game-days/competition/{competition_id}", status_code=303)

#Atualização de Jogadores
@router.post("/update-players/{day_id}")
def update_players(
    day_id: str,
    player_ids: list[str] = Form(...),
    db: Session = Depends(get_db)
):
    day = db.query(GameDay).filter(GameDay.id == day_id).first()

    if not day:
        raise HTTPException(404, "Game Day não encontrado")

    # bloquear se já existem jogos
    has_matches = db.query(Match).filter(
        Match.game_day_id == day_id
    ).count() > 0

    if has_matches:
        raise HTTPException(
            status_code=400,
            detail="Não é possível alterar jogadores após gerar jogos"
        )

    players = db.query(Player).filter(
        Player.id.in_(player_ids)
    ).all()

    day.players = players
    db.commit()

    return RedirectResponse(
        url=f"/game-days/competition/{day.competition_id}",
        status_code=303
    )


# Inscrição de jogador
@router.post("/add-player/{game_day_id}")
def enroll_player(game_day_id: str, player_id: str = Form(...), db: Session = Depends(get_db)):
    add_player(db, game_day_id, player_id)
    # Vamos redirecionar de volta para a página de listagem dos dias da competição
    gd = get_by_id(db, game_day_id)
    return RedirectResponse(f"/game-days/competition/{gd.competition_id}", status_code=303)
    #return RedirectResponse(f"/game-days/view/{game_day_id}", status_code=303)

# Remover jogador
@router.post("/remove-player/{game_day_id}")
def delete_player(game_day_id: str, player_id: str = Form(...), db: Session = Depends(get_db)):
    remove_player(db, game_day_id, player_id)
    # Vamos redirecionar de volta para a página de listagem dos dias da competição
    gd = get_by_id(db, game_day_id)
    return RedirectResponse(f"/game-days/competition/{gd.competition_id}", status_code=303)
    #return RedirectResponse(f"/game-days/view/{game_day_id}", status_code=303)

# Substituir jogador
@router.post("/replace-player/{game_day_id}")
def substitute_player(
    game_day_id: str,
    old_player_id: str = Form(...),
    new_player_id: str = Form(...),
    db: Session = Depends(get_db)
):
    replace_player(db, game_day_id, old_player_id, new_player_id)
    return RedirectResponse(f"/game-days/view/{game_day_id}", status_code=303)

@router.post("/update-fields/{game_day_id}")
def update_fields(game_day_id: str, num_courts: int = Form(...), db: Session = Depends(get_db)):
    gd = get_by_id(db, game_day_id)
    if gd:
        gd.num_courts = max(2, num_courts)  # mínimo 2 campos
        db.commit()
    return RedirectResponse(f"/game-days/competition/{gd.competition_id}", status_code=303)



@router.post("/{game_day_id}/generate-matches")
def generate_matches(game_day_id: str, request: Request, db: Session = Depends(get_db)):

    game_day = db.query(GameDay).filter(GameDay.id == game_day_id).first()
    if not game_day:
        return templates.TemplateResponse(
            "matches.html",
            {
                "request": request,
                "error_msg": "Game day not found",
                "game_day": None,
                "matches": [],
                "summary": {},
                "top3": []
            }
        )

    players = list(game_day.players)
    num_players = len(players)
    required_players = game_day.num_courts * 4

    if num_players != required_players:

        competition = db.query(Competition).filter(Competition.id == game_day.competition_id).first()

        return templates.TemplateResponse(
            "matches.html",
            {
                "request": request,
                "error_msg": f"Número de jogadores insuficiente. Esperado: {required_players}, atual: {num_players}",
                "game_day": game_day,
                "competition": competition,
                "matches": [],
                "summary": {},
                "top3": [],
                "all_players_dict":{}
            }

        )

    existing = db.query(Match).filter(Match.game_day_id == game_day_id).count()
    if existing > 0:
        return templates.TemplateResponse(
            "matches.html",
            {
                "request": request,
                "error_msg": "Já existem jogos gerados para este dia",
                "game_day": game_day,
                "matches": [],
                "summary": {},
                "top3": []
            }
        )

     # 🔁 Round-robin REAL (circle method)
    fixed = players[-1]
    rotating = players[:-1]

    num_rounds = num_players - 1
    matches = []

    for round_number in range(1, num_rounds + 1):

        round_players = rotating + [fixed]

        pairs = []
        for i in range(num_players // 2):
            pairs.append((
                round_players[i],
                round_players[-(i + 1)]
            ))

        # Agrupar pares em jogos (2 pares = 1 campo)
        for court_index in range(game_day.num_courts):
            p1, p2 = pairs[court_index * 2]
            p3, p4 = pairs[court_index * 2 + 1]

            match = Match(
                game_day_id=game_day.id,
                order=round_number,
                scheduled_at=datetime.now(),
                court=court_index + 1,
                team_a_players=f"{p1.id},{p2.id}",
                team_b_players=f"{p3.id},{p4.id}",
                points_team_a=0,
                points_team_b=0
            )

            db.add(match)
            matches.append(match)

        # 🔄 rodar jogadores (menos o fixo)
        rotating = [rotating[-1]] + rotating[:-1]

    db.commit()

    # Redireciona para a página de partidas do dia
    return RedirectResponse(
        url=f"/matches/{game_day_id}/matches",
        status_code=303
    )

@router.post("/{game_day_id}/delete-matches")
def delete_matches(game_day_id: str, db: Session = Depends(get_db)):

    db.query(Match).filter(Match.game_day_id == game_day_id).delete()
    db.commit()

    return RedirectResponse(
        url=f"/matches/{game_day_id}/matches",
        status_code=303
    )