"""
Database connection and session management for WellnessWay Diet Planner
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from typing import Generator
import logging
import time

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Database engine configuration (Lazy)
_engine = None

# Compatibility property (variable that will be set by get_engine)
engine = None

def get_engine():
    global _engine, engine
    if _engine is None:
        settings = get_settings()
        engine_kwargs = {
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
            "pool_timeout": settings.database.pool_timeout,
            "pool_recycle": settings.database.pool_recycle,
            "pool_pre_ping": True,
            "echo": settings.database.echo,
        }
        if settings.is_testing:
            engine_kwargs["poolclass"] = StaticPool
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["poolclass"] = QueuePool
            
        _engine = create_engine(settings.get_database_url(), **engine_kwargs)
        engine = _engine
        
        # Add connection event listeners for monitoring (Bound to specific engine)
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance (if using SQLite)"""
            if "sqlite" in get_settings().get_database_url():
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        @event.listens_for(_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log database connection checkout"""
            if get_settings().logging.level == "DEBUG":
                logger.debug("Database connection checked out")

        @event.listens_for(_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log database connection checkin"""
            if get_settings().logging.level == "DEBUG":
                logger.debug("Database connection checked in")

    return _engine


# Create SessionLocal class (Lazy)
_SessionLocal = None

def get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=get_engine(),
            expire_on_commit=False
        )
    return _SessionLocal

# Create Base class for ORM models
Base = declarative_base()



class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def get_db() -> Generator[Session, None, None]:
        """
        Dependency function to get database session.
        Used with FastAPI's dependency injection system.
        """
        db = get_session_local()()
        start_time = time.time()
        
        try:
            yield db
        except Exception as e:
            logger.error(f"Database session error: {e}")
            db.rollback()
            raise
        finally:
            duration = time.time() - start_time
            if duration > 1.0:  # Log slow queries
                logger.warning(f"Slow database session: {duration:.2f}s")
            db.close()
    
    @staticmethod
    def create_tables():
        """Create all tables in the database"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=get_engine())
        logger.info("Database tables created successfully")
    
    @staticmethod
    def drop_tables():
        """Drop all tables in the database (for testing)"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=get_engine())
        logger.info("Database tables dropped successfully")
    
    @staticmethod
    def check_connection() -> bool:
        """Check if database connection is working"""
        try:
            with get_engine().connect() as connection:
                from sqlalchemy import text
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    @staticmethod
    def get_connection_info() -> dict:
        """Get database connection information"""
        settings = get_settings()
        return {
            "url": settings.get_database_url().split("@")[-1] if "@" in settings.get_database_url() else "hidden",
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow,
            "pool_timeout": settings.database.pool_timeout,
            "pool_recycle": settings.database.pool_recycle,
            "echo": settings.database.echo
        }


# Convenience functions for backward compatibility
def get_db() -> Generator[Session, None, None]:
    """Get database session (backward compatibility)"""
    yield from DatabaseManager.get_db()


def create_tables():
    """Create all tables (backward compatibility)"""
    return DatabaseManager.create_tables()


def drop_tables():
    """Drop all tables (backward compatibility)"""
    return DatabaseManager.drop_tables()


# Initialize database manager
db_manager = DatabaseManager()