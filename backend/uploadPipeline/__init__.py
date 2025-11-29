from logging.handlers import RotatingFileHandler
import eventlet

eventlet.monkey_patch()
import logging
from threading import Thread
from uploadPipeline.config import Config
from flask import Flask, copy_current_request_context
import os
from flask_socketio import SocketIO
from dotenv import load_dotenv
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import (
    JWTManager,
)


load_dotenv()


sock_upload = SocketIO()
mongo = PyMongo()
cors = CORS()
jwt = JWTManager()


def start_consumer():
    from uploadPipeline.video import pop_queue

    pop_queue()


def create_app_upload():
    app = Flask(__name__, static_url_path="/static")

    app.config.from_object(Config)

    app.logger.setLevel(logging.INFO)
    handler = logging.FileHandler("app.log")
    app.logger.addHandler(handler)

    os.makedirs(app.config["UPLOAD_FOLDER_VIDEO"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_IMAGE"], exist_ok=True)

    mongo.init_app(app)
    print(mongo)

    sock_upload.init_app(
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
            "https://192.168.1.132:3001",
        ],
        allow_headers=[
            "Content-Type",
            "Authorization",
        ],
    )

    file_handler = RotatingFileHandler(
        "uploadPipeline.log",
        maxBytes=1024 * 1024 * 10,
        backupCount=10,
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("MyApp startup")

    from .video import video

    app.register_blueprint(video)

    eventlet.spawn(start_consumer)

    return app
