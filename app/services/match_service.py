from sqlalchemy.orm import Session
from app.models.match import Match

def get_by_game_day(db: Session, game_day_id: str):
    return (
        db.query(Match)
        .filter(Match.game_day_id == game_day_id)
        .order_by(Match.order)
        .all()
    )
