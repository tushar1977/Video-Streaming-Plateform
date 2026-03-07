import eventlet

eventlet.monkey_patch()
import os
from uploadPipeline import create_app_upload, sock_upload

env = os.environ.get("FLASK_ENV")

app = create_app_upload()


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development").lower()

    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 3002))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    if env == "prod":
        print(" Running in production mode")
        sock_upload.run(
            app=app,
            host=host,
            port=port,
            debug=False,
            keyfile="/var/.certs/key.pem",
            certfile="/var/.certs/cert.pem",
        )
    else:
        print(" Running in Dev mode")

        sock_upload.run(
            app=app,
            host=host,
            port=port,
            debug=True,
            use_reloader=debug,
        )
