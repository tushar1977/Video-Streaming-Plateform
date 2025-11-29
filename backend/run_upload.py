import os
from uploadPipeline import create_app_upload, sock_upload

env = os.environ.get("FLASK_ENV")

app = create_app_upload()


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        print(" Running in production mode")
    else:
        print(" Running in Development mode")
        host = os.environ.get("FLASK_HOST", "0.0.0.0")
        port = int(os.environ.get("FLASK_PORT", 3002))
        debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

        sock_upload.run(
            app=app,
            host=host,
            port=port,
            debug=True,
            use_reloader=debug,
            keyfile="../.certs/example.com+5-key.pem",
            certfile="../.certs/example.com+5.pem",
        )
