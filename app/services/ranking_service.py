from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.game_day import GameDay

def get_ranking(db: Session, competition_id: str):
    totals = {}

    matches = (
        db.query(Match)
        .join(GameDay)
        .filter(GameDay.competition_id == competition_id)
        .all()
    )

    for m in matches:
        for pid in m.team_a_players.split(","):
            totals[pid] = totals.get(pid, 0) + m.points_team_a
        for pid in m.team_b_players.split(","):
            totals[pid] = totals.get(pid, 0) + m.points_team_b

    return sorted(totals.items(), key=lambda x: x[1], reverse=True)
