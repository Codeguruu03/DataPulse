"""
Database Connection and Session Management for DataPulse Warehouse.
"""

from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datapulse.config import settings
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.warehouse.db")


class DatabaseManager:
    """Manages SQLAlchemy Engine and Session factories."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or self._build_url()
        self._engine = None
        self._session_factory = None

    def _build_url(self) -> str:
        if settings.WAREHOUSE_BACKEND == "postgres":
            return settings.DATABASE_URL
        # Fallback to local embedded SQLite file in data directory
        return f"sqlite:///{settings.BASE_DIR}/data/datapulse_warehouse.db"

    @property
    def engine(self):
        if self._engine is None:
            connect_args = {}
            if self.db_url.startswith("sqlite"):
                connect_args = {"check_same_thread": False}

            self._engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
            )
        return self._session_factory

    def get_session(self) -> Session:
        return self.session_factory()


# Global DB manager singleton (defaults to SQLite fallback if Postgres is not accessible)
default_db_manager = DatabaseManager(
    db_url=f"sqlite:///{settings.BASE_DIR}/data/datapulse_warehouse.db"
)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency provider for DB sessions."""
    session = default_db_manager.get_session()
    try:
        yield session
    finally:
        session.close()
