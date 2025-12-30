from sqlalchemy import Column, String, Date
from app.database import Base
import uuid

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="Por iniciar")  # novo campo
