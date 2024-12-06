from flask import Flask, redirect, url_for
from modules.register_turnover import register_turnover_bp  # Import Register Turnover blueprint
from modules.db_utils import init_db
from modules.ticker_processing import process_tickers
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import os

logging.basicConfig(level=logging.DEBUG, filename='flask.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

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
    # Example task for ASX
    logging.debug('Scheduled task for ASX is running...')
    process_tickers('ASX')
    logging.debug('Scheduled task for ASX completed.')

def scheduled_task_us():
    # Example task for US
    logging.debug('Scheduled task for US is running...')
    process_tickers('US')
    logging.debug('Scheduled task for US completed.')

# Schedule the ASX task at 3:10 PM every day
scheduler.add_job(scheduled_task, 'cron', hour=15, minute=10)

# Schedule the US task at 9:00 AM AEST every day
scheduler.add_job(scheduled_task_us, 'cron', hour=9, minute=0, timezone='Australia/Sydney')

scheduler.start()

if __name__ == "__main__":
    logging.debug("Starting Flask server...")
    if os.getenv('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True)