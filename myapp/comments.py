from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from bson import ObjectId
from .models import Comment
from . import mongo

comm = Blueprint("comm", __name__)


@comm.route("/comment/<string:unique_name>", methods=["POST"])
@jwt_required()
def upload_comment(unique_name):
    data = request.get_json()
    comment_text = data.get("comments") if data else None

    if not comment_text or not comment_text.strip():
        return jsonify({"success": False, "error": "Comment cannot be empty"}), 400

    try:
        user_id = get_jwt_identity()

        comment = Comment(
            text=comment_text.strip(),
            user_id=ObjectId(user_id),
            video_id=unique_name,
        )
        comment_dict = comment.__dict__
        mongo.db.comments.insert_one(comment_dict)

        comment_dict["_id"] = str(comment_dict["_id"])
        comment_dict["user_id"] = str(comment_dict["user_id"])

        return jsonify({"success": True, "comments": [comment_dict]})

    except Exception as e:
        print(f"Error saving comment: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@comm.route("/comment/<string:unique_name>", methods=["GET"])
def get_comments(unique_name):
    try:
        comments_cursor = mongo.db.comments.find({"video_id": unique_name})
        comments = []

        for c in comments_cursor:
            c["_id"] = str(c["_id"])
            c["user_id"] = str(c["user_id"])
            comments.append(c)

        return jsonify({"success": True, "comments": comments})
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
