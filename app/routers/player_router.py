from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.services.player_service import get_all, create, get_by_id, update
from fastapi.templating import Jinja2Templates
from app.models.player import Player
from app.models.match import Match
import uuid
from datetime import datetime

router = APIRouter(prefix="/players")
templates = Jinja2Templates(directory="app/templates")

# Listagem de jogadores
@router.get("/", response_class=HTMLResponse)
def list_players(request: Request, db: Session = Depends(get_db)):
    players = get_all(db)

    jogos = {p.id: 0 for p in players}
    matches = db.query(Match).all()

    for m in matches:
        pida1 = m.team_a_players.split(",")[0]
        pida2 = m.team_a_players.split(",")[1]
        pidb1 = m.team_b_players.split(",")[0]
        pidb2 = m.team_b_players.split(",")[1]
        jogos[pida1] = jogos[pida1] + 1
        jogos[pidb1] = jogos[pidb1] + 1
        jogos[pida2] = jogos[pida2] + 1
        jogos[pidb2] = jogos[pidb2] + 1
    #total_games = get_matches(db)

    return templates.TemplateResponse(
        "players.html",
        {"request": request, "players": players, "matches": jogos}
    )

# Form para criar jogador
@router.get("/new", response_class=HTMLResponse)
def new_player(request: Request):
    return templates.TemplateResponse(
        "player_create.html",
        {"request": request}
    )

@router.post("/new")
def create_player(request: Request, 
                  name: str = Form(...), 
                  sexo: str = Form(...), 
                  nivel: str = Form(...), 
                  data_nascimento = Form(...),
                  db: Session = Depends(get_db)):
    
    name_clean = name.strip()

    # Verifica se já existe jogador com o mesmo nome
    existing = db.query(Player).filter(Player.name.ilike(name_clean)).first()
    if existing:
        # Retorna o template com mensagem de aviso
        context = {
            "request": request,
            "error_message": f"⚠️ Jogador '{name_clean}' já existe!",
            "name": name_clean,
            "sexo": sexo,
            "nivel": nivel,
            "data_nascimento": data_nascimento 
        }
        return templates.TemplateResponse("player_create.html", context)
    
    data_obj = datetime.strptime(data_nascimento, "%Y-%m-%d").date()

    p = Player(id=str(uuid.uuid4()), name=name, sexo=sexo, nivel=nivel, data_nascimento=data_obj)
    db.add(p)
    db.commit()
    return RedirectResponse("/players", status_code=303)

# Form para editar jogador
@router.get("/edit/{player_id}", response_class=HTMLResponse)
def edit_player(request: Request, player_id: str, db: Session = Depends(get_db)):
    player = get_by_id(db, player_id)
    return templates.TemplateResponse(
        "player_edit.html",
        {"request": request, "player": player}
    )

@router.post("/edit/{player_id}")
def update_player(request: Request, player_id: str, 
                  name: str = Form(...), 
                  sexo: str = Form(...), 
                  nivel: str = Form(...), 
                  data_nascimento: str = Form(...),
                  db: Session = Depends(get_db)):
    


    player = db.query(Player).filter(Player.id == player_id).first()
    
    if player:
        # Verifica se já existe outro jogador com o mesmo nome
        existing = db.query(Player).filter(Player.name.ilike(name.strip()), Player.id != player_id).first()
        if existing:
            context = {
                "request": request,
                "error_message": f"⚠️ Jogador '{name}' já existe!",
                "name": name,
                "sexo": sexo,
                "nivel": nivel,
                "player": player
            }
            return templates.TemplateResponse("player_edit.html", context)

        # Atualização
        player.name = name.strip()
        player.sexo = sexo
        player.nivel = nivel
        player.data_nascimento = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        
        db.commit()
    
    return RedirectResponse("/players", status_code=303)

@router.post("/delete/{player_id}")
def delete_player(request: Request, player_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()

    if not player:
        raise HTTPException(status_code=404, detail="Player não encontrado")

    # Verificar se existem jogos
    #matches_count = db.query(Match).filter(
    #or_(
    #    Match.team_a_players.like(f"%{player_id}%"),
    #    Match.team_b_players.like(f"%{player_id}%")
    #)
    #).count()
    
    matches = db.query(Match).all()

    players = get_all(db)

    jogos = {p.id: 0 for p in players}

    for m in matches:
        pida1 = m.team_a_players.split(",")[0]
        pida2 = m.team_a_players.split(",")[1]
        pidb1 = m.team_b_players.split(",")[0]
        pidb2 = m.team_b_players.split(",")[1]
        jogos[pida1] = jogos[pida1] + 1
        jogos[pidb1] = jogos[pidb1] + 1
        jogos[pida2] = jogos[pida2] + 1
        jogos[pidb2] = jogos[pidb2] + 1

    has_matches = jogos[player_id] > 0
    
    if has_matches:
        
        # Retorna o template com mensagem de aviso
        context = {
            "request": request,
            "players": players,
            "matches": jogos,
            "error_message": f"⚠️ Não pode eliminar jogadores com jogos!"
        }
        return templates.TemplateResponse("players.html", context)

    db.delete(player)
    db.commit()

    return RedirectResponse(
        url=f"/players",
        status_code=303
    )