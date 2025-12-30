from sqlalchemy.orm import Session
from app.models.competition import Competition

def get_all(db: Session):
    return db.query(Competition).all()

#novo
def create(db: Session, name, start_date, end_date):
    c = Competition(name=name, start_date=start_date, end_date=end_date)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def get_by_id(db: Session, competition_id: str):
    return db.query(Competition).filter(Competition.id == competition_id).first()

def update_status(db: Session, competition_id: str, status: str):
    competition = db.query(Competition).filter(Competition.id == competition_id).first()
    if competition:
        competition.status = status
        db.commit()
        db.refresh(competition)
    return competition


