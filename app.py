import sys
from flask import Flask, redirect, url_for
from modules.register_turnover import register_turnover_bp  # Import Register Turnover blueprint
from modules.db_utils import init_db
from modules.ticker_processing import process_tickers
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Initialize the database
init_db()

# Register the blueprint
app.register_blueprint(register_turnover_bp, url_prefix='/register_turnover')

# Root route
@app.route("/")
def home():
    return redirect(url_for('register_turnover.register_turnover'))

# Initialize the scheduler
scheduler = BackgroundScheduler()

def scheduled_task():
    # Example task
    print('Scheduled task is running...')
    process_tickers()
    print('Scheduled task completed.')

scheduler.add_job(scheduled_task, 'cron', hour=15, minute=59)  # Run at 3:10 PM every day
scheduler.start()

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True)