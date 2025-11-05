from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET")
    MONGO_URI = os.environ.get("URL")
    UPLOAD_FOLDER_IMAGE = os.path.join(os.getcwd(), "myapp", "static", "img")

    JWT_SECRET_KEY = "ffff"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "None"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = False
    SESSION_COOKIE_DOMAIN = None

    UPLOAD_FOLDER_VIDEO = os.path.join(os.getcwd(), "myapp", "static", "video")
    UPLOAD_EXTENSIONS = [
        ".mp4",
        ".avi",
        ".mov",
        ".jpeg",
        ".png",
        ".jpg",
    ]


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class DevelopmentConfig(Config):
    DEBUG = True
