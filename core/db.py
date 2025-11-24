import sqlite3
import threading
from datetime import datetime


class Database:
    def __init__(self, path='weighbridge_local.db'):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self._setup()

    def _setup(self):
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS logs 
                    (id INTEGER PRIMARY KEY, timestamp TEXT, level TEXT, message TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS readings 
                    (id INTEGER PRIMARY KEY, timestamp TEXT, raw REAL, stable INTEGER)''')
        self.conn.commit()

    def insert_log(self, level, message):
        with self.lock:
            c = self.conn.cursor()
            c.execute('INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)', 
                     (datetime.now().isoformat(), level, message))
            self.conn.commit()

    def insert_reading(self, raw, stable):
        with self.lock:
            c = self.conn.cursor()
            c.execute('INSERT INTO readings (timestamp, raw, stable) VALUES (?, ?, ?)', 
                     (datetime.now().isoformat(), raw, int(stable)))
            self.conn.commit()

    def last_stable_reading(self):
        with self.lock:
            c = self.conn.cursor()
            c.execute('SELECT timestamp, raw FROM readings WHERE stable=1 ORDER BY id DESC LIMIT 1')
            return c.fetchone()