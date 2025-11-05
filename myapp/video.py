import concurrent.futures
from flask import (
    Blueprint,
    abort,
    jsonify,
    make_response,
    request,
    send_from_directory,
    url_for,
    current_app,
)
from flask_jwt_extended import jwt_required
from flask_jwt_extended.utils import get_jwt_identity
from flask_login import current_user
from werkzeug.utils import secure_filename
import os

from myapp.uploadPipeline import (
    Video_Quality,
    create_master_playlist,
    get_file_path,
    get_video_path,
    resize_video,
)

import random
from . import mongo
import string

video = Blueprint("video", __name__)


# -------------------------------
# Serve video metadata
# -------------------------------
@video.route("/api/video/<string:unique_name>", methods=["GET"])
def get_video_data(unique_name):
    video_description = mongo.db.videos.find_one({"unique_name": unique_name})
    if not video_description:
        abort(404)
    likes = list(mongo.db.likes.find({"video_id": unique_name}))
    comments = list(mongo.db.comments.find({"video_id": unique_name}))
    like_count = len(likes)

    user_has_liked = False
    current_user_avatar = None
    current_user_name = None

    if hasattr(current_user, "_id"):
        user_has_liked = any(like.get("user_id") == current_user._id for like in likes)
        current_user_avatar = getattr(current_user, "avatar", None)
        current_user_name = getattr(current_user, "name", None)

    a = jsonify(
        {
            "unique_name": unique_name,
            "like_count": like_count,
            "user_has_liked": user_has_liked,
            "comments": [
                {
                    "id": str(c.get("_id", "")),
                    "user": {
                        "name": c.get("user", {}).get("name", "Anonymous"),
                        "avatar": c.get("user", {}).get(
                            "avatar", "/placeholder.svg?height=40&width=40"
                        ),
                    },
                    "text": c.get("text", ""),
                    "likes": c.get("likes", 0),
                    "created_at": (
                        c.get("created_at", "").isoformat()
                        if hasattr(c.get("created_at"), "isoformat")
                        else str(c.get("created_at", ""))
                    ),
                }
                for c in comments
            ],
            "video_title": video_description.get("title", ""),
            "video_description": video_description.get("description", ""),
            "current_user_avatar": current_user_avatar,
            "current_user_name": current_user_name,
            "total_comments": len(comments),
        }
    )
    return a


# -------------------------------
# Serve master manifest
# -------------------------------
@video.route("/watch/<string:unique_name>/master.m3u8", methods=["GET"])
def serve_hls(unique_name):
    video = mongo.db.videos.find_one({"unique_name": unique_name})
    if not video:
        abort(404)

    master_path = get_video_path(video["file_name"])
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
        print(response)
        return response

    return "Master manifest not found", 404


# -------------------------------
# Serve specific quality playlist
# -------------------------------
@video.route("/watch/<string:unique_name>/Q<string:quality>.m3u8", methods=["GET"])
def serve_quality_playlist(unique_name, quality):
    video_doc = mongo.db.videos.find_one({"unique_name": unique_name})
    if not video_doc:
        abort(404)

    video_path = get_file_path(video_doc["file_name"], quality)
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


# -------------------------------
# Serve TS video segment
# -------------------------------
@video.route("/stream/<string:unique_name>/segment", methods=["GET"])
def serve_segment(unique_name):
    quality = request.args.get("quality")
    segment = request.args.get("segment")

    if not segment:
        return "Segment parameter required", 400

    video_doc = mongo.db.videos.find_one({"unique_name": unique_name})
    if not video_doc:
        abort(404)

    video_path = get_file_path(video_doc["file_name"], quality)
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


# -------------------------------
# Video Upload Route
# -------------------------------
@video.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    try:
        user_id = get_jwt_identity()
        video_title = request.form.get("video_title")
        video_desc = request.form.get("video_desc")
        thumbnail = request.files.get("img")
        file = request.files.get("file")

        if not file or not thumbnail:
            return jsonify({"error": "No file or thumbnail selected"}), 400

        filename = secure_filename(file.filename)
        imgname = secure_filename(thumbnail.filename)
        if not filename or not imgname:
            return jsonify({"error": "File name or thumbnail name is empty"}), 400

        file_ext = os.path.splitext(filename)[1].lower()
        img_ext = os.path.splitext(imgname)[1].lower()
        allowed_extensions = current_app.config["UPLOAD_EXTENSIONS"]

        if file_ext not in allowed_extensions or img_ext not in allowed_extensions:
            return jsonify({"error": "Invalid file extension"}), 400

        base_filename = os.path.splitext(filename)[0]
        video_folder = os.path.join(
            current_app.config["UPLOAD_FOLDER_VIDEO"], base_filename
        )
        os.makedirs(video_folder, exist_ok=True)

        original_path = os.path.join(video_folder, f"original_{filename}")
        file.save(original_path)

        processing_failed = False
        futures = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            for q in Video_Quality:
                quality_path = os.path.join(video_folder, f"{q.name}@{base_filename}")
                hls_folder = os.path.join(quality_path, "hls")
                os.makedirs(hls_folder, exist_ok=True)
                final_path = os.path.join(hls_folder, "stream.m3u8")

                future = executor.submit(
                    resize_video,
                    original_path,
                    final_path,
                    q.value[0],
                    q.value[1],
                    True,
                )
                futures.append((future, quality_path))

            for future, quality_path in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error: {e}")
                    processing_failed = True
                    break

        os.remove(original_path)

        if processing_failed:
            for _, quality_path in futures:
                if os.path.exists(quality_path):
                    try:
                        os.remove(quality_path)
                    except Exception:
                        pass
            return jsonify({"error": "Video processing failed"}), 500

        thumbnail_path = os.path.join(
            current_app.config["UPLOAD_FOLDER_IMAGE"], imgname
        )
        try:
            thumbnail.save(thumbnail_path)
        except Exception:
            for q in Video_Quality:
                quality_path = os.path.join(video_folder, f"{q.name}@{filename}")
                if os.path.exists(quality_path):
                    os.remove(quality_path)
            return jsonify({"error": "Thumbnail saving failed"}), 500

        unique_name = "".join(
            random.choice(string.ascii_letters + string.digits) for _ in range(8)
        )

        create_master_playlist(unique_name, video_folder)

        video_doc = {
            "video_title": video_title,
            "video_desc": video_desc,
            "file_name": base_filename,
            "thumbnail_name": imgname,
            "user_id": user_id,
            "unique_name": unique_name,
        }

        mongo.db.videos.insert_one(video_doc)

        return (
            jsonify(
                {
                    "message": "Upload successful",
                    "video_id": unique_name,
                    "redirect_url": url_for("home.profile"),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({"error": "Internal server error"}), 500
