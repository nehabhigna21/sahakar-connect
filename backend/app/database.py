import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# SQLite is a single file on disk - great for local dev, but most hosts'
# free tiers wipe local files on every restart/redeploy. In production,
# set DATABASE_URL to a real Postgres connection string instead.
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./bluedot.db")

# Render (and some other hosts) hand out URLs starting "postgres://",
# but SQLAlchemy's psycopg2 dialect needs "postgresql://".
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Every ORM model (in models.py) inherits from this so SQLAlchemy knows
# about it and can create the matching table.
Base = declarative_base()


def get_db():
    """FastAPI dependency: opens a DB session for one request, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
