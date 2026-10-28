import os

from flask import Flask


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("GUNSYSTEM_SECRET_KEY") or os.urandom(24).hex()
    if config:
        app.config.update(config)

    from webapp.views import bp

    app.register_blueprint(bp)
    return app
