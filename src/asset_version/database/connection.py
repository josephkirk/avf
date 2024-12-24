from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from typing import Generator
from ..repository.models import Base

class DatabaseConnection:
    def __init__(self, connection_string: str):
        """Initialize database connection
        
        Args:
            connection_string: SQLAlchemy connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(self.engine)
        
    @contextmanager
    def session(self) -> Generator:
        """Provide a transactional scope around a series of operations
        
        Yields:
            SQLAlchemy session
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
