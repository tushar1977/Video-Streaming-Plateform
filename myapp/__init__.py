from flask import Flask, current_app
import os
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from .config import Config as conf
from dotenv import load_dotenv

load_dotenv()


login_manager = LoginManager()
sock = SocketIO()
db = SQLAlchemy()


def create_app(config_class):
    app = Flask(__name__, static_url_path="/static")

    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER_VIDEO"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER_IMAGE"], exist_ok=True)

    db.init_app(app)
    Migrate(app, db)

    sock.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth

    app.register_blueprint(auth)

    from .home import home

    app.register_blueprint(home)

    from .video import video

    app.register_blueprint(video)

    from .comments import comm

    app.register_blueprint(comm)

    from .likes import like

    app.register_blueprint(like)

    return app
