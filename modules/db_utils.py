import sqlite3
import logging
import os
import sys

def init_db():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        db_path = os.path.join(os.path.dirname(sys.executable), 'resources', 'app_data.db')
    else:
        # If the application is run in a normal Python environment
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data.db'))
    
    logging.debug(f"Initializing database at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table for tracking register turnovers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS register_turnover (
            id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            register_turnover REAL NOT NULL,
            cumulative_turnover REAL NOT NULL,
            exchange TEXT NOT NULL
        )
    ''')

    # Create a table for tracking shares on issue (SOI)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soi (
            id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            soi REAL NOT NULL,
            exchange TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def get_db_connection():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle
        db_path = os.path.join(os.path.dirname(sys.executable), 'resources', 'app_data.db')
    else:
        # If the application is run in a normal Python environment
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app_data.db'))
    
    logging.debug(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    return conn

def check_database_contents():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check contents of register_turnover table
    cursor.execute('SELECT * FROM register_turnover')
    register_turnover_rows = cursor.fetchall()
    logging.debug(f"register_turnover table contents: {register_turnover_rows}")
    
    # Check contents of soi table
    cursor.execute('SELECT * FROM soi')
    soi_rows = cursor.fetchall()
    logging.debug(f"soi table contents: {soi_rows}")
    
    conn.close()