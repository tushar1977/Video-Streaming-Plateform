from flask import Blueprint, jsonify, request
from flask_socketio import join_room, leave_room
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson import ObjectId
from . import sock
from .models import mongo

like = Blueprint("like", __name__)


@sock.on("join")
def handle_join(data):
    room = data.get("room")
    if room:
        join_room(room)
        print(f"{request.sid} joined {room}")


@sock.on("leave")
def handle_leave(data):
    room = data.get("room")
    if room:
        leave_room(room)
        print(f"{request.sid} left {room}")


@like.route("/like_action/like/<string:unique_name>", methods=["POST"])
@jwt_required()
def like_action(unique_name):
    user_id = get_jwt_identity()

    existing_like = mongo.db.likes.find_one(
        {"user_id": ObjectId(user_id), "video_id": unique_name}
    )

    if existing_like:
        mongo.db.likes.delete_one(
            {"user_id": ObjectId(user_id), "video_id": unique_name}
        )
    else:
        mongo.db.likes.insert_one(
            {"user_id": ObjectId(user_id), "video_id": unique_name}
        )
        mongo.db.dislikes.delete_one(
            {"user_id": ObjectId(user_id), "video_id": unique_name}
        )

    like_count = mongo.db.likes.count_documents({"video_id": unique_name})
    dislike_count = mongo.db.dislikes.count_documents({"video_id": unique_name})
    user_has_liked = (
        mongo.db.likes.find_one({"video_id": unique_name, "user_id": ObjectId(user_id)})
        is not None
    )
    user_has_disliked = (
        mongo.db.dislikes.find_one(
            {"video_id": unique_name, "user_id": ObjectId(user_id)}
        )
        is not None
    )

    update_data = {
        "type": "like_update",
        "video_id": unique_name,
        "like_count": like_count,
        "dislike_count": dislike_count,
        "user_has_liked": user_has_liked,
        "user_has_disliked": user_has_disliked,
    }

    sock.emit("like_update", update_data, room=f"video_{unique_name}")

    return jsonify(update_data)


@like.route("/like_action/dislike/<string:unique_name>", methods=["POST"])
@jwt_required()
def dislike_action(unique_name):
    user_id = get_jwt_identity()

    existing_dislike = mongo.db.dislikes.find_one(
        {"user_id": ObjectId(user_id), "video_id": unique_name}
    )

    if existing_dislike:
        mongo.db.dislikes.delete_one(
            {"user_id": ObjectId(user_id), "video_id": unique_name}
        )
    else:
        mongo.db.dislikes.insert_one(
            {"user_id": ObjectId(user_id), "video_id": unique_name}
        )
        mongo.db.likes.delete_one(
            {"user_id": ObjectId(user_id), "video_id": unique_name}
        )

    like_count = mongo.db.likes.count_documents({"video_id": unique_name})
    dislike_count = mongo.db.dislikes.count_documents({"video_id": unique_name})
    user_has_liked = (
        mongo.db.likes.find_one({"video_id": unique_name, "user_id": ObjectId(user_id)})
        is not None
    )
    user_has_disliked = (
        mongo.db.dislikes.find_one(
            {"video_id": unique_name, "user_id": ObjectId(user_id)}
        )
        is not None
    )

    update_data = {
        "type": "like_update",
        "video_id": unique_name,
        "like_count": like_count,
        "dislike_count": dislike_count,
        "user_has_liked": user_has_liked,
        "user_has_disliked": user_has_disliked,
    }

    sock.emit("like_update", update_data, room=f"video_{unique_name}")

    return jsonify(update_data)
