from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Reading(Base):
    """
    Database model for weight readings.
    """
    __tablename__ = 'readings'

    id = Column(Integer, primary_key=True)
    weight_kg = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    device_id = Column(Integer, nullable=True)  # For multiple devices
    is_stable = Column(Integer, default=1)  # 1 for stable, 0 for unstable
    session_id = Column(Integer, nullable=True)  # For grouping readings in a session

    def __init__(self, weight_kg, device_id=None, is_stable=True, session_id=None):
        self.weight_kg = weight_kg
        self.device_id = device_id
        self.is_stable = is_stable
        self.session_id = session_id

    def to_dict(self):
        """Convert reading to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'weight_kg': self.weight_kg,
            'timestamp': self.timestamp.isoformat(),
            'device_id': self.device_id,
            'is_stable': bool(self.is_stable),
            'session_id': self.session_id
        }

    @classmethod
    def create_tables(cls, db_url):
        """Create database tables"""
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)

    @classmethod
    def get_session(cls, db_url):
        """Get a new database session"""
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        return Session()