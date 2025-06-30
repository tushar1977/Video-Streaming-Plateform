import os
from myapp import create_app, sock
from myapp.config import DevelopmentConfig, ProductionConfig

env = os.environ.get("FLASK_ENV", "development")

if env == "production":
    app = create_app(ProductionConfig)
    gunicorn_app = app
else:
    app = create_app(DevelopmentConfig)

sock.init_app(app)

if __name__ == "__main__" and env != "production":
    app.run(debug=True, port=3000)
