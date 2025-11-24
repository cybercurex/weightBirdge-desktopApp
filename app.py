from core.config import Config
from core.db import Database
from core.logger import AppLogger
from services.service_manager import ServiceManager
from ui.main_window import MainWindow


class App:
    def __init__(self):
        self.config = Config()
        # Ensure DB_FILE is a valid SQLAlchemy URL
        db_url = self.config.DB_FILE
        if not db_url.startswith("sqlite://"):
            db_url = f"sqlite:///{db_url}"
        self.db = Database(db_url)
        self.logger = AppLogger(self.db)
        self.service_manager = ServiceManager(self.logger, self.db, self.config)
        self.main_window = MainWindow(self.service_manager, self.logger, self.config)

    def run(self):
        # show main window and wire logger callback
        self.logger.set_ui_callback(self.main_window.append_log)
        self.main_window.show()