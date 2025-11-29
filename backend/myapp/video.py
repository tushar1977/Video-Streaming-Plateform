import requests
import json
from myapp.rabbitmq import VideoQueueManager
from flask import (
    Blueprint,
    abort,
    jsonify,
    make_response,
    request,
    send_from_directory,
    current_app,
)
from flask_jwt_extended import jwt_required
from flask_jwt_extended.utils import get_jwt_identity
from flask_login import current_user
from werkzeug.utils import secure_filename
import os

from myapp.uploadPipeline import (
    get_file_path,
    get_video_path,
)
from uploadPipeline.rabbitmq import createChannel

from . import mongo
from . import sock

video = Blueprint("video", __name__)

queue_manager = VideoQueueManager()


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


URL = "https://192.168.1.132:3002/upload"


@video.route("/ping", methods=["GET"])
def test():
    resp = requests.get(URL, verify=False)
    return jsonify(resp.json())


@video.route("/upload", methods=["POST"])
@jwt_required()
def upload():
    try:
        user_id = get_jwt_identity()
        jwt_token = request.headers.get("Authorization")

        video_title = request.form.get("video_title")
        video_desc = request.form.get("video_desc")
        thumbnail = request.files.get("img")
        file = request.files.get("file")

        if not file or not thumbnail:
            return jsonify({"error": "Video file and thumbnail are required"}), 400

        filename = secure_filename(file.filename)
        imgname = secure_filename(thumbnail.filename)

        if not filename or not imgname:
            return jsonify({"error": "Invalid filename"}), 400

        allowed_ext = current_app.config["UPLOAD_EXTENSIONS"]

        file_ext = os.path.splitext(filename)[1].lower()
        img_ext = os.path.splitext(imgname)[1].lower()

        if file_ext not in allowed_ext or img_ext not in allowed_ext:
            return jsonify({"error": "Invalid file extension"}), 400

        base_name = os.path.splitext(filename)[0]

        video_dir = os.path.join(current_app.config["UPLOAD_FOLDER_VIDEO"], base_name)
        thumb_dir = current_app.config["UPLOAD_FOLDER_IMAGE"]

        os.makedirs(video_dir, exist_ok=True)

        video_path = os.path.join(video_dir, f"original_{filename}")
        thumb_path = os.path.join(thumb_dir, imgname)

        file.save(video_path)
        thumbnail.save(thumb_path)

        message_payload = {
            "user_id": user_id,
            "jwt_token": jwt_token,
            "video_title": video_title,
            "video_desc": video_desc,
            "video_path": video_path,
            "thumbnail_path": thumb_path,
            "base_name": base_name,
        }

        job_id = queue_manager.push_video(message_payload)
        queue_stats = queue_manager.get_queue_size()

        print(f"[✓] Video '{base_name}' queued. Job: {job_id}, User: {user_id}")
        print(f"[QUEUE] Pending jobs: {queue_stats}")

        return jsonify(
            {
                "message": "Upload queued successfully",
                "status": "processing",
                "video_title": video_title,
                "queued": True,
            }
        ), 200

    except Exception as e:
        print(f"[UPLOAD ERROR] {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def consume_status_queue():
    channel = createChannel()

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            sock.emit("send_updates", data, room=f"userId_{data['user_id']}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(e)
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue="status_updates", on_message_callback=callback, auto_ack=False
    )
    channel.start_consuming()
