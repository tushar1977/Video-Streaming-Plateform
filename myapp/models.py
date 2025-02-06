from datetime import datetime
from flask_login import UserMixin, current_user
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped
from . import db
import re
import bcrypt
from dataclasses import dataclass


@dataclass
class Video(db.Model):
    video_title: Mapped[str] = db.Column(db.String(100), nullable=False)
    video_desc: Mapped[str] = db.Column(db.String(500), nullable=False)
    file_name: Mapped[str] = db.Column(db.String(100))
    thumbnail_name: Mapped[str] = db.Column(db.String(100))
    unique_name: Mapped[str] = db.Column(
        db.String(10), unique=True, nullable=False, primary_key=True
    )
    user_id: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    comments = db.relationship("Comment", backref="video", lazy=True)
    likes = db.relationship("Likes", backref="video", lazy=True)

    def get_user_like(self):
        if current_user.is_authenticated:
            return Likes.query.filter_by(
                user_id=current_user.id, video_id=self.unique_name
            ).first()
        return None


@dataclass
class Comment(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    text: Mapped[str] = db.Column(db.String(500), nullable=False)
    user_id: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    video_id: Mapped[str] = db.Column(
        db.String(10), db.ForeignKey("video.unique_name"), nullable=False
    )
    created_at: Mapped[datetime] = db.Column(
        db.DateTime, nullable=False, default=db.func.current_timestamp()
    )


@dataclass
class Likes(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)
    like_type: Mapped[str] = db.Column(db.String(7), nullable=False)
    user_id: Mapped[int] = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False
    )
    created_at = db.Column(
        db.DateTime, nullable=False, default=db.func.current_timestamp()
    )
    video_id: Mapped[str] = db.Column(
        db.String(10), db.ForeignKey("video.unique_name"), nullable=False
    )
    __table_args__ = (
        CheckConstraint(like_type.in_(["like", "dislike"]), name="check_like_type"),
    )


@dataclass
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email: Mapped[str] = db.Column(db.String(100), unique=True, nullable=False)
    password: Mapped[str] = db.Column(db.String(1000), nullable=False)
    name: Mapped[str] = db.Column(db.String(1000))
    comments = db.relationship("Comment", backref="user", lazy=True)
    videos = db.relationship("Video", backref="User", lazy=True)
    likes = db.relationship("Likes", backref="User", lazy=True)

    @staticmethod
    def is_valid_email(email):
        allowed_domains = [
            "gmail.com",
            "googlemail.com",
            "yahoo.com",
            "ymail.com",
            "rocketmail.com",
            "outlook.com",
            "hotmail.com",
            "live.com",
            "msn.com",
            "icloud.com",
            "me.com",
            "mac.com",
            "aol.com",
            "protonmail.com",
            "protonmail.ch",
            "zoho.com",
            "zohomail.com",
            "mail.com",
            "email.com",
            "usa.com",
            "europe.com",
            "asia.com",
            "mweb.co.za",
            "online.nl",
            "post.com",
            "shortmail.com",
            "coach.com",
            "consultant.com",
            "engineer.com",
            "doctor.com",
            "gmx.com",
            "gmx.de",
            "gmx.net",
            "yandex.com",
            "yandex.ru",
            "tutanota.com",
            "tutanota.de",
            "mail.ru",
            "list.ru",
            "bk.ru",
            "inbox.ru",
        ]

        # Create the regex pattern
        domain_pattern = "|".join(re.escape(domain) for domain in allowed_domains)
        regex_pattern = rf"^[a-zA-Z0-9_.+-]+@({domain_pattern})$"
        return re.match(regex_pattern, email) is not None

    def check_password(self, password):
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))
