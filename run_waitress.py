from waitress import serve
from app import app
import logging
import os

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    # Determine the port based on the FLASK_ENV environment variable
    port = 5000 if os.getenv('FLASK_ENV') == 'production' else 5001

    # Log the environment and port
    logging.debug(f"FLASK_ENV is set to: {os.getenv('FLASK_ENV')}")
    logging.debug(f"Starting Flask server on port {port}")

    # Start the Flask server using Waitress
    serve(app, host='127.0.0.1', port=port)