import os
from bson import ObjectId
from flask import Blueprint, current_app, jsonify, url_for
from flask_login import current_user, login_required
from .models import mongo

home = Blueprint("home", __name__)


def get_file_path(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER_IMAGE"]
    return os.path.join(upload_folder, filename)


@home.route("/", methods=["GET"])
def index():
    try:
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info",
                }
            },
            {"$unwind": {"path": "$user_info", "preserveNullAndEmptyArrays": True}},
        ]

        videos = list(mongo.db.videos.aggregate(pipeline))

        video_data = []
        for video in videos:
            thumbnail_name = video.get("thumbnail_name")
            if not thumbnail_name:
                continue

            thumbnail_path = os.path.join(
                current_app.static_folder, "img", thumbnail_name
            )
            if not os.path.exists(thumbnail_path):
                continue

            image_url = url_for(
                "static", filename=f"img/{thumbnail_name}", _external=True
            )

            video_data.append(
                {
                    "_id": str(video.get("_id")),
                    "title": video.get("video_title"),
                    "description": video.get("video_desc"),
                    "thumbnail_name": thumbnail_name,
                    "unique_name": video.get("unique_name"),
                    "uploadedAt": video.get("created_at"),
                    "image_url": image_url,
                    "user_id": str(video.get("user_id")),
                    "user_name": (
                        video.get("user_info", {}).get("name")
                        if video.get("user_info")
                        else "Unknown"
                    ),
                }
            )

        return jsonify({"success": True, "videos": video_data}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@home.route("/profile", methods=["GET"])
@login_required
def profile():
    try:
        user = mongo.db.users.find_one({"_id": ObjectId(current_user._id)})

        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404

        videos_cursor = mongo.db.videos.find({"user_id": ObjectId(current_user._id)})
        videos = list(videos_cursor)

        user_videos = []
        for video in videos:
            image_url = url_for(
                "static", filename=f"img/{video.get('thumbnail_name')}", _external=True
            )
            user_videos.append(
                {
                    "_id": str(video.get("_id")),
                    "title": video.get("title"),
                    "description": video.get("description"),
                    "thumbnail_name": video.get("thumbnail_name"),
                    "image_url": image_url,
                }
            )

        return (
            jsonify(
                {
                    "success": True,
                    "user": {
                        "_id": str(user.get("_id")),
                        "name": user.get("name"),
                        "email": user.get("email"),
                    },
                    "videos": user_videos,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
