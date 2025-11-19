import bcrypt


def hash_password(password):
    salt = bcrypt.gensalt(rounds=5)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
