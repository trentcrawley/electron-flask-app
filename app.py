from flask import Flask, redirect, url_for
from modules.register_turnover import register_turnover_bp  # Import Register Turnover blueprint
from modules.db_utils import init_db
from modules.ticker_processing import process_tickers
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
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

# Define the scheduled times for ASX and US tasks
asx_scheduled_time = datetime.now().replace(hour=14, minute=8, second=0, microsecond=0)
us_scheduled_time = datetime.now().replace(hour=14, minute=15, second=0, microsecond=0)

def scheduled_task(scheduled_time):
    # Example task for ASX
    logging.debug('Scheduled task for ASX is running...')
    process_tickers('ASX', scheduled_time)
    logging.debug('Scheduled task for ASX completed.')

def scheduled_task_us(scheduled_time):
    # Example task for US
    logging.debug('Scheduled task for US is running...')
    process_tickers('US', scheduled_time)
    logging.debug('Scheduled task for US completed.')

# Schedule the ASX task at 3:10 PM every day
scheduler.add_job(scheduled_task, 'cron', hour=asx_scheduled_time.hour, minute=asx_scheduled_time.minute, args=[asx_scheduled_time])

# Schedule the US task at 11:03 AM AEST every day
scheduler.add_job(scheduled_task_us, 'cron', hour=us_scheduled_time.hour, minute=us_scheduled_time.minute, timezone='Australia/Sydney', args=[us_scheduled_time])

scheduler.start()

if __name__ == "__main__":
    logging.debug("Starting Flask server...")
    if os.getenv('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True)