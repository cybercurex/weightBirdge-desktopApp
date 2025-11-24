from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Log(Base):
    """
    Database model for logs.
    """
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    level = Column(String, nullable=False)
    message = Column(String, nullable=False)

    def __init__(self, level, message):
        self.level = level
        self.message = message

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'message': self.message
        }

    @classmethod
    def create_tables(cls, db_url):
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)

    @classmethod
    def get_session(cls, db_url):
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        return Session()
