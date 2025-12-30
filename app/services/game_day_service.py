from sqlalchemy.orm import Session
from app.models.game_day import GameDay
from app.models.player import Player
from datetime import date

def get_by_id(db: Session, game_day_id: str):
    """Retorna um GameDay pelo id"""
    return db.query(GameDay).filter(GameDay.id == game_day_id).first()

def get_by_competition(db: Session, competition_id: str):
    return (
        db.query(GameDay)
        .filter(GameDay.competition_id == competition_id)
        .all()
    )

def create(db: Session, competition_id: str, date_obj: date, num_courts: int = 2, group_name = str):
    if num_courts < 2:
        num_courts = 2
    gd = GameDay(competition_id=competition_id, date=date_obj, num_courts=num_courts, group_name=group_name)
    db.add(gd)
    db.commit()
    db.refresh(gd)
    return gd

def add_player(db: Session, game_day_id: str, player_id: str):
    gd = db.query(GameDay).filter(GameDay.id == game_day_id).first()
    player = db.query(Player).filter(Player.id == player_id).first()
    if player not in gd.players:
        gd.players.append(player)
        db.commit()
    return gd

def remove_player(db: Session, game_day_id: str, player_id: str):
    gd = db.query(GameDay).filter(GameDay.id == game_day_id).first()
    player = db.query(Player).filter(Player.id == player_id).first()
    if player in gd.players:
        gd.players.remove(player)
        db.commit()
    return gd

def replace_player(db: Session, game_day_id: str, old_player_id: str, new_player_id: str):
    remove_player(db, game_day_id, old_player_id)
    add_player(db, game_day_id, new_player_id)
