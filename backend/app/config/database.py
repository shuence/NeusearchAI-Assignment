"""Database configuration and session management."""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings
from app.utils.logger import get_logger
from alembic import command
from alembic.config import Config
import os

logger = get_logger("database")

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - enable extensions, run migrations, and create tables."""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        
        # Enable pgvector extension
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
            logger.info("PgVector extension enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension (may already be enabled): {e}")
        
        # Import all models here to ensure they're registered
        from app.models import product  # noqa: F401
        
        # Run Alembic migrations to ensure schema is up to date
        try:
            # Get the path to alembic.ini (should be in the backend directory)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
            
            # Override sqlalchemy.url with our settings
            alembic_cfg.attributes['sqlalchemy.url'] = settings.DATABASE_URL
            
            logger.info("Running database migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.warning(f"Could not run migrations (tables may already exist): {e}")
            # Fall back to create_all if migrations fail
            # This handles the case where alembic_version table doesn't exist yet
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created/verified using create_all")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

