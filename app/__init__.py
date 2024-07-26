import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from pymongo import MongoClient

def create_app():
    app = Flask(__name__)
    # Configure logging
    if not app.debug:
        import os
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    # MongoDB connection
    client = MongoClient("mongodb+srv://pradeepguptagupta9651:gupta@cluster0.cxehmel.mongodb.net/pytest?retryWrites=true&w=majority")
    app.db = client.pytest

    from .routes import main
    app.register_blueprint(main)

    return app
