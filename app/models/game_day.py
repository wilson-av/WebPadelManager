from sqlalchemy import Column, String, Date, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

# Associação GameDay <-> Player (inscritos)
game_day_players = Table(
    'game_day_players',
    Base.metadata,
    Column('game_day_id', String, ForeignKey('game_days.id')),
    Column('player_id', String, ForeignKey('players.id'))
)

class GameDay(Base):
    __tablename__ = "game_days"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competition_id = Column(String, ForeignKey("competitions.id"))
    date = Column(Date, nullable=False)
    num_courts = Column(Integer, nullable=False, default=2)  # mínimo 2

    #groups = Column(Integer, nullable=False, default=1)  # mínimo 1
    groups = Column(String, nullable=True)

    # Jogadores inscritos
    players = relationship("Player", secondary=game_day_players, backref="game_days")
