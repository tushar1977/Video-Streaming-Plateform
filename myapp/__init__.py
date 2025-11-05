import logging
from bson import ObjectId
from flask import Flask, jsonify
import os
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import (
    JWTManager,
)

load_dotenv()


login_manager = LoginManager()
sock = SocketIO()
mongo = PyMongo()
cors = CORS()
jwt = JWTManager()


def create_app(config_class):
    app = Flask(__name__, static_url_path="/static")

    app.config.from_object(config_class)

    app.logger.setLevel(logging.INFO)
    handler = logging.FileHandler("app.log")
    app.logger.addHandler(handler)

    os.makedirs(app.config["UPLOAD_FOLDER_VIDEO"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_IMAGE"], exist_ok=True)

    mongo.init_app(app)

    sock.init_app(
        app,
        cors_allowed_origins="*",
        allow_upgrades=True,
        logger=True,
        engineio_logger=True,
    )
    jwt.init_app(app)
    cors.init_app(
        app,
        supports_credentials=True,
        origins=[
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "https://localhost:3001",
            "http://192.168.1.211:3001",
            "https://192.168.1.211:3001",
        ],
        allow_headers=[
            "Content-Type",
            "Authorization",
        ],
    )
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    from myapp.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

        if user_data:
            return User.from_dict(user_data)
        return None

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        return jsonify({"error": "Unauthorized", "message": "Please log in"}), 401

    from .auth import auth

    app.register_blueprint(auth, url_prefix="/auth")

    from .home import home

    app.register_blueprint(home)

    from .video import video

    app.register_blueprint(video)

    from .comments import comm

    app.register_blueprint(comm)

    from .likes import like

    app.register_blueprint(like)

    return app
