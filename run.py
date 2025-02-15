from myapp import sock, create_app
import os

from flask_socketio import SocketIO

app = create_app()

if __name__ == "__main__":
    gunicorn_app = app

sock.init_app(app)
