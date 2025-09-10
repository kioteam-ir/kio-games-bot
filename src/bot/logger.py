import logging
import sqlite3
import threading
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler

DB_PATH     = 'logs.db' 
MAX_RECORDS = 10000  

# thread-safety
db_lock = threading.Lock()

class DatabaseHandler(logging.Handler):
    def __init__(self, db_path=DB_PATH):
        super().__init__()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    module TEXT,
                    lineno INTEGER,
                    message TEXT,
                    traceback TEXT
                )
            ''')
            conn.commit()
            conn.close()

    def emit(self, record):
        with db_lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM logs')
            count = cursor.fetchone()[0]
            if count > MAX_RECORDS:
                cursor.execute(f'DELETE FROM logs WHERE id <= {count - MAX_RECORDS}')
            

            timestamp = datetime.now().isoformat()
            level     = record.levelname
            module    = record.module
            lineno    = record.lineno
            message   = record.getMessage()
            tb        = traceback.format_exc() if record.exc_info else ''
            
            cursor.execute('''
                INSERT INTO logs (timestamp, level, module, lineno, message, traceback)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, level, module, lineno, message, tb))
            
            conn.commit()
            conn.close()


def setup_logger():
    logger = logging.getLogger('bot_logger')
    logger.setLevel(logging.DEBUG)

    db_handler = DatabaseHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s')
    db_handler.setFormatter(formatter)
    logger.addHandler(db_handler)
    

    file_handler = RotatingFileHandler('bot_logs.log', maxBytes=5*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# logger = setup_logger()
# logger.debug('This is a debug message')
# logger.error('Error occurred', exc_info=True)