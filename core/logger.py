class AppLogger:
    def __init__(self, db):
        self.db = db
        self.ui_callback = None

    def set_ui_callback(self, fn):
        self.ui_callback = fn

    def info(self, message, **kwargs):
        self.db.insert_log('INFO', message)
        if self.ui_callback:
            self.ui_callback('INFO', message)

    def warn(self, message, **kwargs):
        self.db.insert_log('WARN', message)
        if self.ui_callback:
            self.ui_callback('WARN', message)

    def error(self, message, **kwargs):
        self.db.insert_log('ERROR', message)
        if self.ui_callback:
            self.ui_callback('ERROR', message)