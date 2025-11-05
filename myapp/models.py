from flask_login import UserMixin, current_user
from bson import ObjectId
from . import mongo
from dataclasses import dataclass, asdict, field
from datetime import datetime
import bcrypt
import re


@dataclass
class Video:
    video_title: str
    video_desc: str
    file_name: str = ""
    thumbnail_name: str = ""
    views: int = 0
    unique_name: str = ""
    user_id: ObjectId = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        data = asdict(self)
        mongo.db.videos.insert_one(data)
        return data

    def get_user_like(self):
        if current_user.is_authenticated:
            return mongo.db.likes.find_one(
                {"user_id": ObjectId(current_user._id), "video_id": self.unique_name}
            )
        return None


@dataclass
class Comment:
    text: str
    user_id: ObjectId
    video_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        data = asdict(self)
        mongo.db.comments.insert_one(data)
        return data


@dataclass
class Like:
    user_id: ObjectId
    video_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        data = asdict(self)
        mongo.db.likes.insert_one(data)
        return data


@dataclass
class Dislike:
    user_id: ObjectId
    video_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def save(self):
        data = asdict(self)
        mongo.db.dislikes.insert_one(data)
        return data


@dataclass
class User(UserMixin):
    email: str
    password: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    _id: ObjectId = None

    def get_id(self):
        return str(self._id) if self._id else None

    def save(self):
        data = asdict(self)
        if data.get("_id") is None:
            data.pop("_id")

        data["password"] = bcrypt.hashpw(
            self.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        result = mongo.db.users.insert_one(data)
        self._id = result.inserted_id
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email):
        return mongo.db.users.find_one({"email": email})

    @staticmethod
    def find_by_id(user_id):
        return mongo.db.users.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def from_dict(data):
        return User(
            _id=data["_id"],
            name=data["name"],
            email=data.get("email"),
            password=data.get("password"),
        )

    @staticmethod
    def is_valid_email(email):
        allowed_domains = [
            "gmail.com",
            "yahoo.com",
            "outlook.com",
            "hotmail.com",
            "icloud.com",
            "protonmail.com",
            "zoho.com",
            "mail.com",
            "yandex.com",
            "tutanota.com",
        ]
        domain_pattern = "|".join(re.escape(domain) for domain in allowed_domains)
        regex_pattern = rf"^[a-zA-Z0-9_.+-]+@({domain_pattern})$"
        return re.match(regex_pattern, email) is not None
