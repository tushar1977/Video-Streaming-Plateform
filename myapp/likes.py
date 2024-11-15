from flask import Blueprint, jsonify, render_template, request, url_for
from flask_login import current_user, login_required
from flask_login.login_manager import flash, redirect
from sqlalchemy.sql.operators import like_op
from . import db
from .models import Like, Video

like = Blueprint("like", __name__)


@like.route("/like_action/<string:like_action>/<string:unique_name>", methods=["POST"])
@login_required
def like_action(like_action, unique_name):
    video = Video.query.filter_by(unique_name=unique_name).first_or_404()
    existing_like = Like.query.filter_by(
        user_id=current_user.id, video_id=unique_name
    ).first()

    liked = False
    
    if like_action == "like":
        if existing_like:
            db.session.delete(existing_like)
            liked = False
        else:
            new_like = Like(
                user_id=current_user.id, video_id=unique_name, like_type="like"
            )
            db.session.add(new_like)
            liked = True
    else:
        if existing_like:
            db.session.delete(existing_like)
            liked = False

    db.session.commit()
    
    likes = Like.query.filter_by(video_id=unique_name).all()
    user_has_liked = any(like.user_id == current_user.id for like in likes)
    like_count = len(likes)
    
    # Return updated HTML rather than JSON
    return render_template(
        'like_section.html', 
        like_count=like_count, 
        user_has_liked=user_has_liked, 
        unique_name=unique_name
    )
@like.route("/like_action/get_likes/<string:unique_name>", methods=["GET"])
@login_required
def get_likes(unique_name):
    # Find the video by unique_name
    video = Video.query.filter_by(unique_name=unique_name).first_or_404()

    # Query for likes based on unique_name
    likes = Like.query.filter_by(video_id=unique_name).all()
    like_count = len(likes)

    # Check if the current user has liked the video
    user_has_liked = any(like.user_id == current_user.id for like in likes)

    # Return rendered HTML for the like section
    return render_template(
        'like_section.html',  # This is the template that includes the updated like count and button
        like_count=like_count,
        user_has_liked=user_has_liked,
        unique_name=unique_name
    )
