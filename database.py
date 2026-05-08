# Import Statements
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Set up logger
load_dotenv()
logger = logging.getLogger(__name__)

#Declare Database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Check if URL is valid
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Railway provides postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()