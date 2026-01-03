"""
Database Connection Module

This module handles the SQLAlchemy database connection to SQL Server.
It provides:
- Connection string configuration using environment variables
- SQLAlchemy engine and session factory
- FastAPI dependency for database session injection
- Test mode support for XLSX-based testing
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from app.config import DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_DRIVER, TEST_MODE


# Only create real database connection when not in test mode
if not TEST_MODE:
    # Build the MSSQL connection string using pyodbc driver
    # The pool_pre_ping option ensures connections are validated before use
    connection_string = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}/{DB_NAME}?driver={DB_DRIVER.replace(' ', '+')}"
    )

    # Create SQLAlchemy engine with connection pooling
    engine = create_engine(connection_string, pool_pre_ping=True)

    # Session factory for creating database sessions
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    # In test mode, we don't need a real database connection
    engine = None
    SessionLocal = None


def get_db():
    """
    FastAPI dependency that provides a database session.
    
    In test mode, yields None (the mock query function handles data loading).
    In production mode, yields a database session and ensures it's properly 
    closed after the request completes.
    
    Usage:
        @app.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db)):
            # use db here
    """
    if TEST_MODE:
        # In test mode, yield None - the query function uses XLSX files
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()