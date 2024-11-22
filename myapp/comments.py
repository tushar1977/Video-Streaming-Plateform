from flask.helpers import url_for
from flask_login import current_user, login_required
from flask_login.login_manager import flash
from .models import User, Video, Comment, Likes
from flask import Blueprint, redirect, render_template, request
from . import db

comm = Blueprint("comm", __name__)


@comm.route("/watch/<string:unique_name>", methods=["POST"])
@login_required
def upload_comment(unique_name):
    comment_text = request.form.get("comments")
    print(comment_text)
    if comment_text:
        try:
            comment = Comment(
                text=comment_text, user_id=current_user.id, video_id=unique_name
            )
            db.session.add(comment)
            db.session.commit()
            flash("Your comment has been posted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(
                "An error occurred while posting your comment. Please try again.",
                "error",
            )
    else:
        flash("Comment cannot be empty.", "warning")

    return redirect(url_for("video.watch_video", unique_name=unique_name))
