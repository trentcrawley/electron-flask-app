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

def process_tickers():
    tickers = get_scanner_tickers(scan_number=5, exchange="ASX")
    now = datetime.now()
    cutoff_time = now.replace(hour=16, minute=35, second=0, microsecond=0)
    #cutoff_time = now.replace(hour=16, minute=31, second=0, microsecond=0)

    def wait_and_process():
        while datetime.now() < cutoff_time:
            time.sleep(30)

        for ticker in tickers:
            ticker_with_exchange = f"{ticker}.AX"
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
                            WHERE ticker = ?
                            ORDER BY date DESC
                            LIMIT 1
                        ''', (ticker,))
                        result = cursor.fetchone()

                        if result:
                            prior_cumulative_turnover = result['cumulative_turnover']
                            cumulative_turnover = prior_cumulative_turnover + register_turnover
                        else:
                            cumulative_turnover = register_turnover

                        # Insert register turnover data
                        cursor.execute('''
                            INSERT INTO register_turnover (ticker, date, register_turnover, cumulative_turnover)
                            VALUES (?, ?, ?, ?)
                        ''', (ticker, now.strftime('%Y-%m-%d'), register_turnover, cumulative_turnover))

                        # Insert SOI data
                        cursor.execute('''
                            INSERT INTO soi (ticker, date, soi)
                            VALUES (?, ?, ?)
                        ''', (ticker, now.strftime('%Y-%m-%d'), shares_outstanding))

                        conn.commit()
                        conn.close()

    # Run the waiting and processing logic in a separate thread
    threading.Thread(target=wait_and_process).start()

    #TODO: make table interactive so can delete and add to db
    # change db so has event_date i.e date added and don't present id, so we can double click
    # add us
    # 


