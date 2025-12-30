from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from app.database import Base
import uuid

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_day_id = Column(String, ForeignKey("game_days.id"))

    order = Column(Integer, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    court = Column(Integer, nullable=False)

    team_a_players = Column(String, nullable=False)  # CSV
    team_b_players = Column(String, nullable=False)

    points_team_a = Column(Integer, nullable=False)
    points_team_b = Column(Integer, nullable=False)
