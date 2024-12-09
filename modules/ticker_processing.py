import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from modules.ibscannerdata import get_scanner_tickers
import time
import threading
import os
import subprocess
import logging

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
    print(db_path)
    return db_path

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def process_tickers(exchange="ASX", scheduled_time=None):
    print(f"Starting process_tickers for exchange: {exchange} at {datetime.now()}")
    tickers = get_scanner_tickers(scan_number=6, exchange=exchange)
    print(f"Tickers to process: {tickers}")
    now = datetime.now()
    if scheduled_time:
        cutoff_time = scheduled_time + timedelta(minutes=1)
    else:
        if exchange == "US":
            cutoff_time = now.replace(hour=9, minute=35, second=0, microsecond=0)
        else:
            cutoff_time = now.replace(hour=16, minute=35, second=0, microsecond=0)
    print(f"Cutoff time set to: {cutoff_time}")

    def wait_and_process():
        while datetime.now() < cutoff_time:
            print(f"Waiting... Current time: {datetime.now()}, Cutoff time: {cutoff_time}")
            time.sleep(3)

        for ticker in tickers:
            ticker_with_exchange = f"{ticker}.AX" if exchange == "ASX" else ticker
            print(f"Processing ticker: {ticker_with_exchange}")
            stock_data = yf.Ticker(ticker_with_exchange)
            history = stock_data.history(period="1d")

            if not history.empty:
                print(f"Getting data from yfinance for {ticker_with_exchange}")
                shares_outstanding = stock_data.info.get('sharesOutstanding', 'N/A')
                if shares_outstanding != 'N/A':
                    latest_volume = history['Volume'].iloc[-1]
                    register_turnover = (latest_volume / shares_outstanding) * 100
                    print(f"Register turnover for {ticker_with_exchange}: {register_turnover}%")

                    if register_turnover >= 4:  # Threshold for register turnover
                        conn = get_db_connection()
                        cursor = conn.cursor()

                        # Check if the ticker already exists in the database
                        cursor.execute('''
                            SELECT cumulative_turnover FROM register_turnover
                            WHERE ticker = ? AND exchange = ?
                            ORDER BY date DESC
                            LIMIT 1
                        ''', (ticker, exchange))
                        result = cursor.fetchone()

                        if result:
                            prior_cumulative_turnover = result['cumulative_turnover']
                            cumulative_turnover = prior_cumulative_turnover + register_turnover
                        else:
                            cumulative_turnover = register_turnover

                        if result:
                            # Update the existing entry
                            cursor.execute('''
                                UPDATE register_turnover
                                SET date = ?, register_turnover = ?, cumulative_turnover = ?
                                WHERE ticker = ? AND exchange = ?
                            ''', (now.strftime("%Y-%m-%d"), register_turnover, cumulative_turnover, ticker, exchange))
                            print(f"Updated existing entry for {ticker_with_exchange}")
                        else:
                            # Insert a new entry
                            cursor.execute('''
                                INSERT INTO register_turnover (ticker, date, register_turnover, cumulative_turnover, exchange)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (ticker, now.strftime("%Y-%m-%d"), register_turnover, cumulative_turnover, exchange))
                            print(f"Inserted new entry for {ticker_with_exchange}")

                        # Insert SOI data
                        cursor.execute('''
                            INSERT INTO soi (ticker, date, soi, exchange)
                            VALUES (?, ?, ?, ?)
                        ''', (ticker, now.strftime('%Y-%m-%d'), shares_outstanding, exchange))
                        print(f"Inserted SOI data for {ticker_with_exchange}")

                        conn.commit()
                        conn.close()

    # Run the wait_and_process function in a separate thread
    threading.Thread(target=wait_and_process).start()