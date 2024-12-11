import sqlite3
import logging
import os
import sys
import subprocess

def get_current_git_branch():
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            logging.error(f"Error determining Git branch: {result.stderr}")
            return None
    except Exception as e:
        logging.error(f"Exception determining Git branch: {e}")
        return None

def get_db_path():
    branch = get_current_git_branch()
    if branch == 'development':
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data_dev.db'))
    elif branch == 'master':
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data.db'))
    else:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data_other.db'))
    return db_path

def get_db_connection():
    db_path = get_db_path()
    print(f"Connecting to database at {db_path}")  # Print the database path for debugging
    logging.debug(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db_path = get_db_path()
    logging.debug(f"Initializing database at {db_path}")
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

def check_database_contents():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check contents of register_turnover table
    cursor.execute('SELECT * FROM register_turnover')
    register_turnover_rows = cursor.fetchall()
    register_turnover_data = [dict(row) for row in register_turnover_rows]  # Convert rows to dictionaries
    logging.debug(f"register_turnover table contents: {register_turnover_data}")
    print(f"register_turnover table contents: {register_turnover_data}")
    
    # Check contents of soi table
    cursor.execute('SELECT * FROM soi')
    soi_rows = cursor.fetchall()
    soi_data = [dict(row) for row in soi_rows]  # Convert rows to dictionaries
    logging.debug(f"soi table contents: {soi_data}")
    print(f"soi table contents: {soi_data}")
    
    conn.close()

# Uncomment the following line to check database contents during debugging
#check_database_contents()