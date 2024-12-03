import sqlite3

def init_db():
    conn = sqlite3.connect('app_data.db')
    cursor = conn.cursor()

    # Create a table for tracking register turnovers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS register_turnover (
            id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            register_turnover REAL NOT NULL,
            cumulative_turnover REAL NOT NULL
        )
    ''')

    # Create a table for tracking shares on issue (SOI)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soi (
            id INTEGER PRIMARY KEY,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            soi REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()