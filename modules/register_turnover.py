from flask import Blueprint, render_template, request, jsonify, redirect
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sqlite3

register_turnover_bp = Blueprint('register_turnover', __name__)

def get_db_connection():
    conn = sqlite3.connect('app_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@register_turnover_bp.route("/", methods=["GET", "POST"])
def register_turnover():
    today = datetime.today().strftime("%Y-%m-%d")
    ticker, exchange, start_date, end_date = "", "", today, today

    # Step 1: Load tracking data from SQLite
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM register_turnover")
    tracking_data = cursor.fetchall()
    conn.close()

    # Convert database rows into an HTML table
    if tracking_data:
        tracking_df = pd.DataFrame(
            tracking_data,
            columns=["id", "ticker", "date", "register_turnover", "cumulative_turnover"],
        )
        tracking_df["delete"] = tracking_df["id"].apply(
            lambda id: f'<button class="delete-btn" data-id="{id}" style="color: red; border: none; background: none;">&times;</button>'
        )
        tracking_html = tracking_df.to_html(
            index=False,
            classes="table table-striped",
            columns=[
                "id",
                "ticker",
                "date",
                "register_turnover",
                "cumulative_turnover",
                "delete",
            ],
            escape=False,
        )
    else:
        tracking_html = "<p>No tracking data found.</p>"

    # Step 2: Handle Plotly chart generation
    plot_html = ""
    if request.method == "POST" and 'generate_plot' in request.form:
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

    return render_template(
        "index.html",
        plot_html=plot_html,
        today=today,
        ticker=ticker,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        tracking_html=tracking_html,
        tracking_data=tracking_data,
    )

@register_turnover_bp.route("/add_ticker", methods=["POST"])
def add_ticker():
    ticker = request.form.get("new_ticker")
    date = request.form.get("date")
    if not ticker or not date:
        return jsonify(success=False, error="Ticker and Date are required"), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO register_turnover (ticker, date, register_turnover, cumulative_turnover)
            VALUES (?, ?, ?, ?)
            """,
            (ticker, date, 0, 0),
        )
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print(f"Error adding ticker: {e}")
        return jsonify(success=False, error=str(e)), 500


@register_turnover_bp.route("/delete/<int:row_id>", methods=["POST"])
def delete_row(row_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM register_turnover WHERE id = ?", (row_id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        print(f"Error deleting row: {e}")
        return jsonify(success=False, error=str(e)), 500