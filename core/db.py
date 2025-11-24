
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.reading import Reading, Base as ReadingBase
from models.log import Log, Base as LogBase
import threading
from datetime import datetime

class Database:
    def __init__(self, path='sqlite:///weighbridge_local.db'):
        self.engine = create_engine(path, connect_args={"check_same_thread": False})
        self.Session = sessionmaker(bind=self.engine)
        self.lock = threading.Lock()
        self._setup()

    def _setup(self):
        # Create tables for both logs and readings
        ReadingBase.metadata.create_all(self.engine)
        LogBase.metadata.create_all(self.engine)

    def insert_log(self, level, message):
        with self.lock:
            session = self.Session()
            log = Log(level=level, message=message)
            session.add(log)
            session.commit()
            session.close()

    def insert_reading(self, raw, stable):
        with self.lock:
            session = self.Session()
            reading = Reading(weight_kg=raw, is_stable=stable)
            session.add(reading)
            session.commit()
            session.close()

    def last_stable_reading(self):
        with self.lock:
            session = self.Session()
            reading = session.query(Reading).filter_by(is_stable=1).order_by(Reading.id.desc()).first()
            session.close()
            if reading:
                return (reading.timestamp.isoformat(), reading.weight_kg)
            return None