import os
import secrets
from datetime import datetime, timedelta
from smtplib import SMTP
import random
from flask_mailman import Mail
import bcrypt
from dotenv import load_dotenv
from flask import Blueprint, flash, render_template, request, session
from flask.helpers import url_for
from flask_login import login_user, logout_user
from werkzeug.utils import redirect

from . import db
from .config import Config
from .models import User

load_dotenv()
conf = Config()
mail = Mail()

auth = Blueprint("auth", __name__)


@auth.route("/signup")
def signup():
    return render_template("signup.html")


@auth.route("/signup", methods=["POST"])
def signup_post():
    global otp
    # code to validate and add user to database goes here
    email = request.form.get("email")

    if not User.is_valid_email(email):
        flash("Not Valid Email")
        return redirect(url_for("auth.signup"))

    name = request.form.get("name")
    password = request.form.get("password")

    if len(str(password)) <= 6:
        flash("Password should be greater than 6 characters")

    if not email or not password or not name:
        flash("Email and password are required")
    user = User.query.filter_by(email=email).first()
    if user:
        flash("Email already exist")
        return redirect(url_for("auth.signup"))

    otp = random.randint(100000, 999999)
    otp_expiry = datetime.utcnow() + timedelta(minutes=10)

    salt = bcrypt.gensalt(rounds=5)

    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    session["signup_data"] = {
        "email": email,
        "name": name,
        "password": hashed,
        "otp": str(otp),
        "otp_expiry": otp_expiry,
    }

    print("done session data")

    with SMTP(conf.MAIL_SERVER, conf.MAIL_PORT) as con:
        con.starttls()
        con.login(user="codewithmrpy@gmail.com", password="eaflyqlwydcznrgt")

        con.sendmail(
            from_addr="",
            to_addrs=str(email),
            msg=f"subject:Your signup OTP \n\n {otp}",
        )

    return redirect(url_for("auth.verify_otp"))


@auth.route("/api/v1/otp")
def verify_otp():
    if "signup_data" not in session:
        return redirect(url_for("auth.signup"))
    return render_template("otp.html")


@auth.route("/api/v1/otp", methods=["POST"])
def verify_otp_post():
    if "signup_data" not in session:
        return redirect(url_for("auth.signup"))

    signup_data = session["signup_data"]
    user_otp = request.form.get("otp-input")

    if datetime.utcnow() > signup_data["otp_expiry"]:
        flash("OTP expired!!")
        session.pop("signup_data")
        return redirect(url_for("auth.signup"))

    if user_otp != signup_data["otp"]:
        flash("Invalid OTP!! Try again")
        return redirect(url_for("auth.verify_otp"))

    try:
        new_user = User(
            email=signup_data["email"],
            name=signup_data["name"],
            password=signup_data["password_hash"],
        )
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error creating account. Please try again.")
        return redirect(url_for("auth.signup"))
    finally:
        session.pop("signup_data")

    flash("Account created successfully! Please log in.")
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
