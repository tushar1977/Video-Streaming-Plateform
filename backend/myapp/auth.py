from flask import Blueprint, request, jsonify
from flask_jwt_extended.utils import create_access_token, unset_jwt_cookies
from . import mongo
from .models import User
from myapp.utils.checkPass import hash_password
import bcrypt

auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["POST"])
def signup_post():
    data = request.get_json()
    email = data.get("email")
    name = data.get("name")
    password = data.get("password")

    if not email or not password or not name:
        return (
            jsonify(
                {"success": False, "message": "Email, name, and password are required."}
            ),
            400,
        )

    existing_user = mongo.db.users.find_one({"email": email})
    if existing_user:
        return jsonify({"success": False, "message": "Email already exists."}), 400

    hashed_pw = hash_password(password)
    result = mongo.db.users.insert_one(
        {
            "email": email,
            "name": name,
            "password": hashed_pw,
        }
    )

    user = User(
        _id=str(result.inserted_id),
        email=email,
        password=hashed_pw,
        name=name,
    )
    access_token = create_access_token(identity=str(user._id))

    return (
        jsonify(
            {
                "success": True,
                "message": "Account created successfully!",
                "user": {"id": str(user._id), "name": user.name, "email": user.email},
                "access_token": access_token,
            }
        ),
        201,
    )


@auth.route("/login", methods=["POST"])
def login_check():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user_data = mongo.db.users.find_one({"email": email})
    if not user_data:
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    if not bcrypt.checkpw(
        password.encode("utf-8"), user_data["password"].encode("utf-8")
    ):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    user = User(
        _id=str(user_data["_id"]),
        email=user_data["email"],
        password=user_data["password"],
        name=user_data.get("name"),
    )

    access_token = create_access_token(identity=str(user._id))
    return jsonify(
        {
            "success": True,
            "message": "Login successful!",
            "user": {"id": str(user._id), "name": user.name, "email": user.email},
            "access_token": access_token,
        }
    )


@auth.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response
