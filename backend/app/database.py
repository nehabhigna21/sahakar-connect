from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite is just a single file on disk (bluedot.db) - no separate database
# server to install or run, which is why it's ideal for a prototype.
SQLALCHEMY_DATABASE_URL = "sqlite:///./bluedot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # SQLite normally only allows the thread that created a connection to use
    # it; FastAPI can handle a request on a different thread, so we relax that.
    connect_args={"check_same_thread": False},
)

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
