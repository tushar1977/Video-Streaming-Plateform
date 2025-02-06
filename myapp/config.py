import os
from dotenv import load_dotenv

load_dotenv()

username = os.environ.get("DB_USERNAME")
password = os.environ.get("DB_PASSWORD")
hostname = os.environ.get("DB_HOSTNAME")
database = os.environ.get("DB_NAME")
port = os.environ.get("DB_PORT", 3306)  # Default to 3306 if not specified


class Config:
    SECRET_KEY = os.getenv("SECRET")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{username}:{password}@{hostname}:{port}/{database}"
    )
    UPLOAD_FOLDER_IMAGE = os.path.join(os.getcwd(), "myapp", "static", "img")
    SEND_FILE_MAX_AGE_DEFAULT = 0

    MAIL_PORT = 587
    MAIL_SERVER = "smtp.google.com"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }
    UPLOAD_FOLDER_VIDEO = os.path.join(os.getcwd(), "myapp", "static", "video")
    UPLOAD_EXTENSIONS = [
        ".mp4",
        ".avi",
        ".mov",
        ".jpeg",
        ".png",
        ".jpg",
    ]
