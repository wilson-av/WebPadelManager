from sqlalchemy import Column, String, Date
from app.database import Base
import uuid
from datetime import date

class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    sexo = Column(String, nullable=True)   # M ou F
    nivel = Column(String, nullable=True)  # M1, F1, M2, etc.
    data_nascimento = Column(Date, nullable=False)


    @property
    def idade(self) -> int:
        if not self.data_nascimento:
            return None

        today = date.today()
        return (
            today.year
            - self.data_nascimento.year
            - (
                (today.month, today.day)
                < (self.data_nascimento.month, self.data_nascimento.day)
            )
        )
