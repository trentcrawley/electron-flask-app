from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import subprocess
import os
from loguru import logger
import time

register_turnover_bp = Blueprint('register_turnover', __name__)

# Configure loguru logger
log_file_path = os.path.join(os.getcwd(), 'logs', 'register_turnover.log')
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
    logger.debug(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def execute_query_with_retry(query, params=(), retries=5, delay=0.1):
    for attempt in range(retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.commit()
            conn.close()
            return results
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logger.warning(f"Database is locked, retrying... ({attempt + 1}/{retries})")
                time.sleep(delay)
            else:
                raise
    raise sqlite3.OperationalError("Max retries reached, database is still locked")

@register_turnover_bp.route("/", methods=["GET", "POST"])
def register_turnover():
    logger.debug("register_turnover function called")
    today = datetime.today().strftime("%Y-%m-%d")
    ticker, exchange, start_date, end_date = "", "", today, today

    # Step 1: Load tracking data from SQLite
    logger.debug("Loading tracking data from SQLite")
    
    # Fetch ASX stocks
    asx_data = execute_query_with_retry("SELECT ticker, date AS tracked_since, register_turnover AS turnover_today, cumulative_turnover FROM register_turnover WHERE exchange = 'ASX' ORDER BY turnover_today DESC")
    logger.debug(f"ASX data loaded: {asx_data}")

    # Fetch US stocks
    us_data = execute_query_with_retry("SELECT ticker, date AS tracked_since, register_turnover AS turnover_today, cumulative_turnover FROM register_turnover WHERE exchange = 'US' ORDER BY turnover_today DESC")
    logger.debug(f"US data loaded: {us_data}")

    # Convert database rows into HTML tables
    # Convert database rows into HTML tables
    if asx_data:
        asx_df = pd.DataFrame(
            asx_data,
            columns=["ticker", "tracked_since", "turnover_today", "cumulative_turnover"],
        )
        asx_df["delete"] = asx_df.apply(
            lambda row: f'<button class="delete-btn" data-ticker="{row["ticker"]}" data-date="{row["tracked_since"]}" style="color: red; border: none; background: none;">&times;</button>',
            axis=1
        )
        asx_html = asx_df.to_html(
            index=False,
            classes="table table-striped",
            columns=[
                "ticker",
                "tracked_since",
                "turnover_today",
                "cumulative_turnover",
                "delete",
            ],
            escape=False,
        )
    else:
        asx_html = "<p>No ASX tracking data found.</p>"
    logger.debug(f"ASX HTML generated: {asx_html}")

    if us_data:
        us_df = pd.DataFrame(
            us_data,
            columns=["ticker", "tracked_since", "turnover_today", "cumulative_turnover"],
        )
        us_df["delete"] = us_df.apply(
            lambda row: f'<button class="delete-btn" data-ticker="{row["ticker"]}" data-date="{row["tracked_since"]}" style="color: red; border: none; background: none;">&times;</button>',
            axis=1
        )
        us_html = us_df.to_html(
            index=False,
            classes="table table-striped",
            columns=[
                "ticker",
                "tracked_since",
                "turnover_today",
                "cumulative_turnover",
                "delete",
            ],
            escape=False,
        )
    else:
        us_html = "<p>No US tracking data found.</p>"
    logger.debug(f"US HTML generated: {us_html}")

    # Step 2: Handle Plotly chart generation
    plot_html = ""
    if request.method == "POST" and 'generate_plot' in request.form:
        logger.debug("Generating Plotly chart")
        ticker = request.form.get("ticker")
        exchange = request.form.get("exchange")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        end_date = (
            datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        ticker_with_exchange = f"{ticker}.{exchange}" if exchange else ticker
        stock_data = yf.Ticker(ticker_with_exchange)
        history = stock_data.history(start=start_date, end=end_date)
        logger.debug(f"Stock history data: {history}")

        if not history.empty:
            # Get shares outstanding
            shares_outstanding = stock_data.info.get("sharesOutstanding", "N/A")
            register_turnover = (
                (history["Volume"] / shares_outstanding).cumsum()
                if shares_outstanding != "N/A"
                else None
            )

            # VWAP calculation
            typical_price = (
                history["High"] + history["Low"] + history["Close"]
            ) / 3
            vwap = (typical_price * history["Volume"]).cumsum() / history[
                "Volume"
            ].cumsum()
            latest_register_turnover = (
                register_turnover.iloc[-1] * 100
                if register_turnover is not None
                else 0
            )

            # Create subplots with secondary y-axis for Register Turnover
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                row_heights=[0.7, 0.3],
                vertical_spacing=0.05,
                specs=[[{"secondary_y": True}], [{}]],
            )

            # Add Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=history.index,
                    open=history["Open"],
                    high=history["High"],
                    low=history["Low"],
                    close=history["Close"],
                    name="Candlestick",
                ),
                row=1,
                col=1,
            )

            # Add VWAP line
            fig.add_trace(
                go.Scatter(
                    x=history.index,
                    y=vwap,
                    mode="lines",
                    name="VWAP",
                    line=dict(color="orange"),
                ),
                row=1,
                col=1,
            )

            # Add Register Turnover
            if register_turnover is not None:
                fig.add_trace(
                    go.Scatter(
                        x=history.index,
                        y=register_turnover,
                        mode="lines+markers",
                        name="Register Turnover",
                        line=dict(color="green"),
                    ),
                    row=1,
                    col=1,
                    secondary_y=True,
                )

            # Add Volume bar chart
            fig.add_trace(
                go.Bar(
                    x=history.index, y=history["Volume"], name="Volume"
                ),
                row=2,
                col=1,
            )

            fig.update_layout(
                template="plotly_dark",
                plot_bgcolor="black",
                paper_bgcolor="black",
                font_color="white",
                title=f"{ticker} Register Turnover: {latest_register_turnover:.2f}%",
                xaxis_rangeslider_visible=False,
                height=750,
            )

            fig.update_xaxes(type="category")
            fig.update_yaxes(
                title_text="Price", secondary_y=False, row=1, col=1
            )
            fig.update_yaxes(
                title_text="Register Turnover", secondary_y=True, row=1, col=1
            )

            plot_html = fig.to_html(full_html=False)
            logger.debug(f"Plot HTML generated: {plot_html}")

    return render_template(
        "index.html",
        plot_html=plot_html,
        today=today,
        ticker=ticker,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        asx_html=asx_html,
        us_html=us_html,
    )

@register_turnover_bp.route("/add_ticker", methods=["POST"])
def add_ticker():
    ticker = request.form.get("new_ticker")
    date = request.form.get("date")
    exchange = request.form.get("exchange").upper()  # Normalize exchange to uppercase
    if not ticker or not date or not exchange:
        return jsonify(success=False, error="Ticker, Date, and Exchange are required"), 400

    try:
        execute_query_with_retry('''
            INSERT INTO register_turnover (ticker, date, register_turnover, cumulative_turnover, exchange)
            VALUES (?, ?, 0, 0, ?)
        ''', (ticker, date, exchange))
        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error adding ticker: {e}")
        return jsonify(success=False, error=str(e)), 500

@register_turnover_bp.route("/delete/<ticker>/<date>", methods=["POST"])
def delete_ticker(ticker, date):
    try:
        execute_query_with_retry('DELETE FROM register_turnover WHERE ticker = ? AND date = ?', (ticker, date))
        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error deleting ticker: {e}")
        return jsonify(success=False, error=str(e)), 500