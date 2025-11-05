import os
from myapp import create_app, sock
from myapp.config import DevelopmentConfig, ProductionConfig

env = os.environ.get("FLASK_ENV")

if env == "production":
    app = create_app(ProductionConfig)
else:
    app = create_app(DevelopmentConfig)


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        print(" Running in production mode")
    else:
        print(" Running in Development mode")
        host = os.environ.get("FLASK_HOST", "0.0.0.0")
        port = int(os.environ.get("FLASK_PORT", 3000))
        debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

        sock.run(
            app=app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            keyfile="./.certs/localhost+2-key.pem",
            certfile="./.certs/localhost+2.pem",
        )
