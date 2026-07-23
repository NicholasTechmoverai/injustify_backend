import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import Config

logger = logging.getLogger(__name__)

db_url = Config.DATABASE_URL

# Ensure SQLite path uses check_same_thread=False if SQLite
connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    logger.warning(f"Primary DB connection ({db_url}) failed: {e}. Falling back to SQLite.")
    db_url = Config.SQLITE_URL
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """ Dependency for getting DB session in FastAPI routes """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_health():
    """ Checks DB status and latency for system monitoring """
    start_time = time.time()
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "dialect": engine.name,
            "connected": True
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "latency_ms": 0.0,
            "error": str(e),
            "connected": False
        }
