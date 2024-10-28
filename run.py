from myapp import sock, create_app
import os

from flask_socketio import SocketIO

app = create_app()

if __name__ == "__main__":
    sock.run(
        app,
        host="0.0.0.0",
        debug=True,
        allow_unsafe_werkzeug=True,
        port=int(os.getenv("PORT", 6000)),
    )
