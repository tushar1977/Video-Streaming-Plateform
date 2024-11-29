import cv2
from flask import (
    Blueprint,
    Response,
    make_response,
    render_template,
    request,
    redirect,
    send_file,
    send_from_directory,
    url_for,
    current_app,
)
from flask.helpers import flash
from flask_login import login_required, current_user
from flask_socketio import emit
from werkzeug.utils import secure_filename
import os

from .models import Likes, Video, Comment
import random
from . import db
from . import sock
import string
import re
import subprocess
from enum import Enum

video = Blueprint("video", __name__)


class Video_Quality(Enum):
    Q480 = [854, 480]
    Q720 = [1280, 720]
    Q1080 = [1920, 1080]


def get_chunk(file_path, byte1=None, byte2=None):
    file_size = os.stat(file_path).st_size
    start = 0 if byte1 is None else byte1
    end = file_size - 1 if byte2 is None else byte2
    length = end - start + 1

    with open(file_path, "rb") as f:
        f.seek(start)
        chunk = f.read(length)

    return chunk, start, end, file_size


def get_file_path(
    filename,
    quality,
):
    upload_folder = current_app.config["UPLOAD_FOLDER_VIDEO"]
    return os.path.join(upload_folder, filename, f"Q{quality}@{filename}", "hls")


def get_video_path(
    filename,
):
    upload_folder = current_app.config["UPLOAD_FOLDER_VIDEO"]
    return os.path.join(upload_folder, filename)


def resize_video(input_path, output_path, width, height):
    segment_dir = os.path.dirname(output_path)
    os.makedirs(segment_dir, exist_ok=True)
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-vf",
        f"scale={width}:{height}",
        "-c:v",
        "libx264",
        "-crf",
        "30",
        "-b:v",
        "1200k",
        "-movflags",
        "+faststart",  # Ensures moov atom is at the start for smooth playback
        "-c:a",
        "aac",
        "-hls_time",
        "4",
        "-hls_playlist_type",
        "vod",
        "-hls_segment_filename",
        os.path.join(segment_dir, "segment_%03d.ts"),
        "-hls_flags",
        "independent_segments",
        "-f",
        "hls",
        "-y",
        output_path,
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    print(result.stdout)


def get_bitrate_for_quality(quality: Video_Quality) -> int:
    """Calculate appropriate bitrate for each quality"""
    bitrate_map = {
        Video_Quality.Q480: 1000,  # 1000k for 480p
        Video_Quality.Q720: 2500,  # 2500k for 720p
        Video_Quality.Q1080: 5000,  # 5000k for 1080p
    }
    return bitrate_map[quality]


def create_master_playlist(unique_name, output_dir: str, base_filename: str):
    master_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"

    for quality in Video_Quality:
        width, height = quality.value
        bitrate = get_bitrate_for_quality(quality)

        quality_url = f"/watch/{unique_name}/{quality.name}.m3u8"

        total_bandwidth = (bitrate + 128) * 1000
        master_content += f'#EXT-X-STREAM-INF:BANDWIDTH={total_bandwidth},RESOLUTION={width}x{height},CODECS="avc1.64001f,mp4a.40.2"\n'
        master_content += f"{quality_url}\n\n"

    master_path = os.path.join(output_dir, "master.m3u8")
    with open(master_path, "w") as f:
        f.write(master_content)

    return master_path


@video.route("/watch/<string:unique_name>", methods=["GET"])
def watch_video(unique_name):
    likes = Likes.query.filter_by(video_id=unique_name).all()
    comments = Comment.query.filter_by(video_id=unique_name).all()
    video_description = Video.query.filter_by(unique_name=unique_name).first_or_404()
    like_count = len(likes)
    user_has_liked = any(like.user_id == current_user.id for like in likes)
    return render_template("watch.html", unique_name=unique_name, like_count=like_count, 
                           user_has_liked=user_has_liked,comments=comments, video_description=video_description)


@video.route("/watch/<string:unique_name>/master.m3u8", methods=["GET"])
def serve_hls(unique_name):
    video = Video.query.filter_by(unique_name=unique_name).first_or_404()
    master_path = get_video_path(video.file_name)
    master_manifest_path = os.path.join(master_path, "master.m3u8")
    print(master_manifest_path)

    if os.path.isfile(master_manifest_path):
        with open(master_manifest_path, "r") as f:
            master_content = f.read()

        response = make_response(master_content)
        response.headers.update(
            {
                "Content-Type": "application/vnd.apple.mpegurl",
                "Access-Control-Allow-Origin": "*",
            }
        )
        return response

    return "Master manifest not found", 404


@video.route("/watch/<string:unique_name>/Q<string:quality>.m3u8", methods=["GET"])
def serve_quality_playlist(unique_name, quality):
    video = Video.query.filter_by(unique_name=unique_name).first_or_404()
    video_path = get_file_path(video.file_name, quality)
    manifest_path = os.path.join(video_path, "stream.m3u8")

    if os.path.isfile(manifest_path):
        with open(manifest_path, "r") as f:
            content = f.read()

        modified_content = []
        for line in content.splitlines():
            if line.endswith(".ts"):
                segment_name = line.strip()
                segment_url = f"/stream/{unique_name}/segment?quality={quality}&segment={segment_name}"
                modified_content.append(segment_url)
            else:
                modified_content.append(line)

        response = make_response("\n".join(modified_content))
        response.headers.update(
            {
                "Content-Type": "application/vnd.apple.mpegurl",
                "Access-Control-Allow-Origin": "*",
            }
        )
        return response

    return "Quality manifest not found", 404


@video.route("/stream/<string:unique_name>/segment", methods=["GET"])
def serve_segment(unique_name):
    quality = request.args.get("quality")
    segment = request.args.get("segment")

    if not segment:
        return "Segment parameter required", 400

    video = Video.query.filter_by(unique_name=unique_name).first_or_404()
    video_path = get_file_path(video.file_name, quality)
    segment_path = os.path.join(video_path, segment)

    if os.path.isfile(segment_path):
        response = make_response(send_from_directory(video_path, segment))
        response.headers.update(
            {
                "Content-Type": "video/MP2T",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
            }
        )
        return response

    return "Segment not found", 404


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

        filename = secure_filename(str(file.filename))
        imgname = secure_filename(str(thumbnail.filename))
        if not filename or not imgname:
            flash("File name or thumbnail name is empty")
            return redirect(url_for("video.upload"))

        file_ext = os.path.splitext(filename)[1].lower()
        img_ext = os.path.splitext(imgname)[1].lower()
        allowed_extensions = current_app.config["UPLOAD_EXTENSIONS"]

        if file_ext not in allowed_extensions or img_ext not in allowed_extensions:
            flash("Invalid file extension")
            return redirect(url_for("video.upload"))

        base_filename = os.path.splitext(filename)[0]
        video_folder = os.path.join(
            current_app.config["UPLOAD_FOLDER_VIDEO"], base_filename
        )
        os.makedirs(video_folder, exist_ok=True)

        original_path = os.path.join(video_folder, f"original_{filename}")
        file.save(original_path)

        processing_failed = False
        processed_files = []

        for q in Video_Quality:
            quality_path = os.path.join(video_folder, f"{q.name}@{base_filename}")
            hls_folder = os.path.join(quality_path, "hls")
            os.makedirs(hls_folder, exist_ok=True)
            final_path = os.path.join(hls_folder, "stream.m3u8")

            try:
                resize_video(original_path, final_path, q.value[0], q.value[1])
            except Exception as e:
                flash(f"Video processing failed for {q.name}")
                processing_failed = True
                break
        os.remove(original_path)
        if processing_failed:
            if os.path.exists(original_path):
                os.remove(original_path)
            for processed_file in processed_files:
                if os.path.exists(processed_file):
                    os.remove(processed_file)
            return redirect(url_for("video.upload"))
        thumbnail_path = os.path.join(
            current_app.config["UPLOAD_FOLDER_IMAGE"], imgname
        )
        try:
            thumbnail.save(thumbnail_path)
        except Exception as e:
            flash("Thumbnail saving failed")
            for q in Video_Quality:
                quality_path = os.path.join(video_folder, f"{q.name}@{filename}")
                if os.path.exists(quality_path):
                    os.remove(quality_path)
            return redirect(url_for("video.upload"))

        unique_name = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(8)
        )

        create_master_playlist(unique_name, video_folder, base_filename)
        new_video = Video(
            video_title=str(video_title),
            video_desc=str(video_desc),
            file_name=base_filename,
            thumbnail_name=imgname,
            user_id=current_user.id,
            unique_name=unique_name,
        )

        try:
            db.session.add(new_video)
            db.session.commit()
            flash("Upload successful")
            return redirect(url_for("home.profile", video_id=new_video.unique_name))
        except Exception as e:
            flash("Error saving video details to database")
            print(f"Database error: {e}")
            return "Internal server error", 500

    return render_template("upload.html")
