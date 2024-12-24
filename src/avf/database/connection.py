from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ..repository.models import Base


class DatabaseConnection:
    def __init__(self, connection_string: str) -> None:
        """Initialize database connection

        Args:
            connection_string: SQLAlchemy connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables"""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Generator[Session, Any, None]:
        """Provide a transactional scope around a series of operations

        Yields:
            SQLAlchemy session
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()
