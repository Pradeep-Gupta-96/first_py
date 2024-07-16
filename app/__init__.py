from flask import Flask
from pymongo import MongoClient

def create_app():
    app = Flask(__name__)

    # MongoDB connection
    client = MongoClient("mongodb+srv://pradeepguptagupta9651:gupta@cluster0.cxehmel.mongodb.net/pytest?retryWrites=true&w=majority")
    app.db = client.pytest

    from .routes import main
    app.register_blueprint(main)

    return app
