from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

#DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./padel.db")

# Example for PostgreSQL
DATABASE_URL = "postgresql://padeldb_ekmh_user:Tk633PGsQnCy37eMyYJWFpVgh57Gm5co@dpg-d59hj3uuk2gs73e7876g-a.virginia-postgres.render.com/padeldb_ekmh"
# postgresql://padeldb_ekmh_user:Tk633PGsQnCy37eMyYJWFpVgh57Gm5co@dpg-d59hj3uuk2gs73e7876g-a/padeldb_ekmh"

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    connect_args = {"sslmode": "require"}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#DATABASE_URL = "sqlite:///./padel.db"
# For SQLite (uncomment if using SQLite)
