"""
Database Connection and Session Management for DataPulse Warehouse.
"""

from pathlib import Path
from typing import Optional, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from datapulse.config import settings
from datapulse.utils.logger import get_logger

logger = get_logger("datapulse.warehouse.db")


class DatabaseManager:
    """Manages SQLAlchemy Engine and Session factories with automated SQLite fallback."""

    def __init__(self, db_url: Optional[str] = None):
        self._custom_url = db_url
        self.db_url = db_url or self._build_url()
        self._engine = None
        self._session_factory = None

    def _build_url(self) -> str:
        sqlite_file = settings.BASE_DIR / "data" / "datapulse_warehouse.db"
        sqlite_file.parent.mkdir(parents=True, exist_ok=True)

        if settings.WAREHOUSE_BACKEND == "postgres":
            # Attempt to use postgres url
            return settings.DATABASE_URL
        return f"sqlite:///{sqlite_file}"

    @property
    def engine(self):
        if self._engine is None:
            connect_args = {}
            if self.db_url.startswith("sqlite"):
                connect_args = {"check_same_thread": False}
                db_path_str = self.db_url.replace("sqlite:///", "")
                if db_path_str and db_path_str != ":memory:":
                    try:
                        Path(db_path_str).parent.mkdir(parents=True, exist_ok=True)
                    except Exception:
                        pass

            try:
                engine = create_engine(
                    self.db_url,
                    pool_pre_ping=True,
                    connect_args=connect_args,
                )
                # Test connectivity
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1;"))
                self._engine = engine
            except Exception as e:
                logger.warning(
                    f"Could not connect to warehouse database at {self.db_url} ({e}). "
                    "Falling back to local embedded SQLite database."
                )
                sqlite_file = settings.BASE_DIR / "data" / "datapulse_warehouse.db"
                sqlite_file.parent.mkdir(parents=True, exist_ok=True)
                self.db_url = f"sqlite:///{sqlite_file}"
                self._engine = create_engine(
                    self.db_url,
                    connect_args={"check_same_thread": False},
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


# Global DB manager singleton
default_db_manager = DatabaseManager()


def get_db_session() -> Generator[Session, None, None]:
    """Dependency provider for DB sessions."""
    session = default_db_manager.get_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
