import cv2
from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
)
from flask.helpers import flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from .models import Like, Video, Comment
import random
from . import db
import string
import re
import subprocess

video = Blueprint("video", __name__)


def get_chunk(file_path, byte1=None, byte2=None):
    file_size = os.stat(file_path).st_size
    start = 0 if byte1 is None else byte1
    end = file_size - 1 if byte2 is None else byte2
    length = end - start + 1

    with open(file_path, "rb") as f:
        f.seek(start)
        chunk = f.read(length)

    return chunk, start, end, file_size


def get_file_path(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER_VIDEO"]
    return os.path.join(upload_folder, filename)


def resize_video(input_path, output_path, width, height):
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-vf",
        f"scale={width}:{height}",
        "-c:a",
        "copy",
        "-y",
        output_path,
    ]
    subprocess.run(command, check=True)


@video.route("/watch/<string:unique_name>", methods=["GET"])
def watch_video(unique_name):
    video = Video.query.filter_by(unique_name=unique_name).first_or_404()
    comments = (
        Comment.query.filter_by(video_id=unique_name)
        .order_by(Comment.created_at.desc())
        .all()
    )
    likes = Like.query.filter_by(video_id=unique_name).all()
    video_url = f"/watch/{video.unique_name}"
    print(video_url)
    print(video.file_name)
    return render_template(
        "watch.html",
        video=video,
        video_url=video_url,
        comments=comments,
        likes=likes,
    )


@video.route("/stream/<string:unique_name>", methods=["GET"])
def stream_video(unique_name):
    video = Video.query.filter_by(unique_name=unique_name).first_or_404()
    file_path = get_file_path(video.file_name)
    print(file_path)
    range_header = request.headers.get("Range", None)
    byte1, byte2 = 0, None

    if range_header:
        match = re.search(r"(\d+)-(\d*)", range_header)
        if match:
            groups = match.groups()
            byte1, byte2 = int(groups[0]), (int(groups[1]) if groups[1] else None)

    chunk, start, end, file_size = get_chunk(file_path, byte1, byte2)

    resp = Response(chunk, 206, mimetype="video/mp4", content_type="video/mp4")
    resp.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
    print(resp.headers)
    return resp


@video.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        video_title = request.form.get("video_title")
        video_desc = request.form.get("video_desc")
        thumbnail = request.files.get("img")
        file = request.files.get("file")
        if not file or not thumbnail:
            flash("No file or thumbnail selected")
            return redirect(url_for("video.upload"))

        filename = secure_filename(file.filename)
        imgname = secure_filename(thumbnail.filename)
        if filename == "" or imgname == "":
            flash("File name or thumbnail name is empty")
            return redirect(url_for("video.upload"))

        file_ext = os.path.splitext(filename)[1].lower()
        img_ext = os.path.splitext(imgname)[1].lower()
        if (
            file_ext not in current_app.config["UPLOAD_EXTENSIONS"]
            or img_ext not in current_app.config["UPLOAD_EXTENSIONS"]
        ):
            flash("Invalid file extension")
            return redirect(url_for("video.upload"))

        temp_path = os.path.join(
            current_app.config["UPLOAD_FOLDER_VIDEO"], f"temp_{filename}"
        )
        final_path = os.path.join(current_app.config["UPLOAD_FOLDER_VIDEO"], filename)

        try:
            file.save(temp_path)

            resize_video(temp_path, final_path, 800, 500)

            os.remove(temp_path)
        except Exception as e:
            flash("Video processing failed")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(final_path):
                os.remove(final_path)
            return redirect(url_for("video.upload"))

        try:
            thumbnail.save(
                os.path.join(current_app.config["UPLOAD_FOLDER_IMAGE"], imgname)
            )
        except Exception as e:
            flash("Thumbnail saving failed")
            if os.path.exists(final_path):
                os.remove(final_path)
            return redirect(url_for("video.upload"))

        password = "".join(
            random.choice(string.ascii_letters + string.digits) for i in range(8)
        )
        new_video = Video(
            video_title=video_title,
            video_desc=video_desc,
            file_name=filename,
            thumbnail_name=imgname,
            user_id=current_user.id,
            unique_name=password,
        )
        try:
            db.session.add(new_video)
            db.session.commit()
            flash("Upload successful")
            return redirect(url_for("home.profile", video_id=new_video.unique_name))
        except Exception as e:
            flash("Error saving video details to database")
            print(f"Database error: {e}")
            if os.path.exists(final_path):
                os.remove(final_path)
            return "Internal server error", 500

    return render_template("upload.html")
