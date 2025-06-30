import os
import time

from flask import Blueprint, current_app, redirect, send_from_directory, url_for
from flask.templating import render_template
from flask_login import current_user, login_required
from .models import User, Video

home = Blueprint("home", __name__)


def get_file_path(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER_IMAGE"]
    return os.path.join(upload_folder, filename)


@home.route("/", methods=["GET"])
def index():
    videos = Video.query.all()
    print(videos)
    video_data = []
    for video in videos:
        image_url = url_for("static", filename=f"img/{video.thumbnail_name}")
        video_data.append({"video": video, "image_url": image_url})
    return render_template("index.html", video_data=video_data)


@home.route("/profile", methods=["GET"])
@login_required
def profile():
    user = User.query.get(current_user.id)
    videos = Video.query.filter_by(user_id=current_user.id).all()
    return render_template("profile.html", name=user.name, videos=videos)
