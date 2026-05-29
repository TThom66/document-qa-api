# Import Statements
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Set up logger
load_dotenv()
logger = logging.getLogger(__name__)

#Declare Database URL
# Railway sometimes uses different variable names
DATABASE_URL = (
    os.getenv("DATABASE_URL") or
    os.getenv("POSTGRES_URL") or
    os.getenv("PGURL")
)

# Check if URL is valid
if not DATABASE_URL:
    raise ValueError(
        "No database URL found. Set DATABASE_URL environment variable."
    )

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

logger.info(f"Connecting to database: {DATABASE_URL[:20]}...")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()