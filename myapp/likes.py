from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user, login_required
from . import db
from .models import Likes

like = Blueprint("like", __name__)


@like.route("/like_action/<string:like_action>/<string:unique_name>", methods=["POST"])
@login_required
def like_action(like_action, unique_name):
    existing_like = Likes.query.filter_by(
        user_id=current_user.id, video_id=unique_name
    ).first()

    if like_action == "like":
        if existing_like:
            db.session.delete(existing_like)
        else:
            new_like = Likes(
                user_id=current_user.id, video_id=unique_name, like_type="like"
            )
            db.session.add(new_like)
    else:
        if existing_like:
            db.session.delete(existing_like)

    db.session.commit()

    likes = Likes.query.filter_by(video_id=unique_name).all()
    user_has_liked = any(like.user_id == current_user.id for like in likes)
    like_count = len(likes)

    return render_template(
        "like_section.html",
        like_count=like_count,
        user_has_liked=user_has_liked,
        unique_name=unique_name,
    )


@like.route("/like_action/get_likes/<string:unique_name>", methods=["GET"])
@login_required
def get_likes(unique_name):
    likes = Likes.query.filter_by(video_id=unique_name).all()
    like_count = len(likes)

    user_has_liked = any(like.user_id == current_user.id for like in likes)

    return render_template(
        "like_section.html",
        like_count=like_count,
        user_has_liked=user_has_liked,
        unique_name=unique_name,
    )
