import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from the .env file.
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./learning.db",
)

connect_args = {}

# Add SQLite-specific connection settings.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False
    }

# Create the database engine.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

# Create database sessions for running queries.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Create the base class for database models.
Base = declarative_base()


# Create and provide a database session for each request.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()