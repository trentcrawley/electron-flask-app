import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from modules.ibscannerdata import get_scanner_tickers
import time
import threading

def get_db_connection():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def process_tickers(exchange="ASX"):
    tickers = get_scanner_tickers(scan_number=6, exchange=exchange)
    now = datetime.now()
    if exchange == "US":
        cutoff_time = now.replace(hour=9, minute=35, second=0, microsecond=0)
    else:
        cutoff_time = now.replace(hour=16, minute=35, second=0, microsecond=0)

    def wait_and_process():
        while datetime.now() < cutoff_time:
            time.sleep(30)

        for ticker in tickers:
            ticker_with_exchange = f"{ticker}.AX" if exchange == "ASX" else ticker
            stock_data = yf.Ticker(ticker_with_exchange)
            history = stock_data.history(period="1d")

            if not history.empty:
                shares_outstanding = stock_data.info.get('sharesOutstanding', 'N/A')
                if shares_outstanding != 'N/A':
                    latest_volume = history['Volume'].iloc[-1]
                    register_turnover = (latest_volume / shares_outstanding) * 100

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
                        else:
                            # Insert a new entry
                            cursor.execute('''
                                INSERT INTO register_turnover (ticker, date, register_turnover, cumulative_turnover, exchange)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (ticker, now.strftime("%Y-%m-%d"), register_turnover, cumulative_turnover, exchange))

                        # Insert SOI data
                        cursor.execute('''
                            INSERT INTO soi (ticker, date, soi)
                            VALUES (?, ?, ?)
                        ''', (ticker, now.strftime('%Y-%m-%d'), shares_outstanding))

                        conn.commit()
                        conn.close()

    # Run the wait_and_process function in a separate thread
    threading.Thread(target=wait_and_process).start()