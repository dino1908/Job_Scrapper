"""
Database configuration and session management.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import all models here to ensure they are registered with Base
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()
    print("✅ Database tables created successfully")


def drop_db():
    """Drop all database tables. USE WITH CAUTION!"""
    from . import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    print("🗑️  Database tables dropped")


def _run_lightweight_migrations():
    """Apply lightweight SQLite schema updates for backward compatibility."""
    if "sqlite" not in settings.DATABASE_URL:
        return

    inspector = inspect(engine)

    try:
        job_columns = {column["name"] for column in inspector.get_columns("jobs")}
    except Exception:
        return

    if "posted_date" not in job_columns:
        with engine.connect() as connection:
            connection.execute(text("ALTER TABLE jobs ADD COLUMN posted_date DATETIME"))
            connection.commit()
        print("✅ Migration applied: added jobs.posted_date")
