from flask import Blueprint, flash, render_template, request
from flask.helpers import url_for
from werkzeug.utils import redirect
from . import db
from .models import User
import bcrypt
from flask_login import login_user, logout_user

auth = Blueprint("auth", __name__)


@auth.route("/signup")
def signup():
    return render_template("signup.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    # code to validate and add user to database goes here
    email = request.form.get("email")

    if not User.is_valid_email(email):
        flash("Not Valid Email")
        return redirect(url_for("auth.signup"))

    name = request.form.get("name")
    password = request.form.get("password")

    if len(password) <= 6:
        flash("Password should be greater than 6 characters")

    if not email or not password or not name:
        flash("Email and password are required")
    user = User.query.filter_by(email=email).first()
    if user:
        flash("Email already exist")
        return redirect(url_for("auth.signup"))

    salt = bcrypt.gensalt(rounds=5)

    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)

    new_user = User(
        email=email,
        name=name,
        password=hashed,
    )
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for("auth.login"))


@auth.route("/login")
def login():
    return render_template("login.html")


@auth.route("/login", methods=["POST"])
def login_check():
    email = request.form.get("email")
    password = request.form.get("password")
    remember = True if request.form.get("remember") else False


    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        flash("Please check your login details and try again.")
        return redirect(url_for("auth.login"))

    login_user(user, remember=remember)
    return redirect(url_for("home.index"))


@auth.route("/logout")
def logout():
    logout_user()

    return redirect(url_for("auth.login"))
