from sqlalchemy.orm import Session
from app.models.player import Player

def get_all(db: Session):
    return db.query(Player).all()

def get_by_id(db: Session, player_id: str):
    return db.query(Player).filter(Player.id == player_id).first()

def create(db: Session, name: str):
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player

def update(db: Session, player_id: str, name: str):
    player = get_by_id(db, player_id)
    if player:
        player.name = name
        db.commit()
        db.refresh(player)
    return player
