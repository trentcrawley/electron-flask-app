import sqlite3
import os
import subprocess
from loguru import logger

# Configure loguru logger
log_file_path = os.path.join(os.getcwd(), 'logs', 'db_utils.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
logger.add(log_file_path, level="DEBUG", format="{time} - {level} - {message}")

def get_current_git_branch():
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logger.error(f"Error determining Git branch: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Exception determining Git branch: {e}")
        return None

def get_db_path():
    branch = get_current_git_branch()
    if branch == 'development':
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data_dev.db'))
    elif branch == 'master':
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data.db'))
    else:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data_other.db'))
    logger.debug(f"Database path: {db_path}")
    return db_path

def get_db_connection():
    db_path = get_db_path()
    print(f"Connecting to database at {db_path}")  # Print the database path for debugging
    logger.debug(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_path = get_db_path()
    logger.debug(f"Initializing database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table for tracking register turnovers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS register_turnover (
            ticker TEXT NOT NULL,
            date DATETIME NOT NULL,
            register_turnover REAL NOT NULL,
            cumulative_turnover REAL NOT NULL,
            exchange TEXT NOT NULL,
            PRIMARY KEY (date, ticker)
        )
    ''')

    # Create a table for tracking shares on issue (SOI)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soi (
            ticker TEXT NOT NULL,
            date DATETIME NOT NULL,
            soi REAL NOT NULL,
            exchange TEXT NOT NULL,
            PRIMARY KEY (date, ticker)
        )
    ''')

    conn.commit()
    conn.close()
    logger.debug("Database initialized successfully")