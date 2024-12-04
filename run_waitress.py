from waitress import serve
from app import app
import logging

#logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    #logging.debug("Starting server with waitress...")
    serve(app, host='127.0.0.1', port=5000)