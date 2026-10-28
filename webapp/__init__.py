import os

from flask import Flask, redirect, session, url_for

from webapp import ronovo_sso
from webapp.players import Players

PROGRESS_KEYS = ("range", "destroyed")


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("GUNSYSTEM_SECRET_KEY") or os.urandom(24).hex()
    app.config["DATA_DIR"] = os.environ.get("DATA_DIR", "data")
    if config:
        app.config.update(config)

    from webapp.views import bp

    app.register_blueprint(bp)
    if ronovo_sso.enabled():
        add_ronovo_login(app)
    return app


def add_ronovo_login(app: Flask) -> None:
    """The range and destroyed count live in the browser's session cookie. While logged in with Ronovo
    they are also kept for the account, and logging in on another browser takes whichever copy is newer."""
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    players = Players(os.path.join(app.config["DATA_DIR"], "players.db"))

    def progress():
        return {key: session.get(key) for key in PROGRESS_KEYS}

    def ronovo_login(account):
        stored = players.load(account["sub"])
        if stored:
            saved, saved_at = stored
            if saved_at > session.get("saved_at", 0):
                session.pop("range", None)
                if saved.get("range"):
                    session["range"] = saved["range"]
                session["saved_at"] = saved_at
            session["destroyed"] = max(session.get("destroyed", 0), saved.get("destroyed") or 0)
        session.permanent = True
        session["ronovo_sub"] = account["sub"]
        session["ronovo_user"] = account["username"]
        players.store(account["sub"], progress(), session.get("saved_at", 0))
        return redirect(url_for("main.menu"))

    ronovo_sso.add_flask_routes(app, "gunsystem", ronovo_login)

    @app.post("/logout")
    def logout():
        session.pop("ronovo_sub", None)
        session.pop("ronovo_user", None)
        return redirect(url_for("main.menu"))

    @app.context_processor
    def inject_ronovo():
        return {"ronovo": True}

    @app.after_request
    def save_progress(response):
        if session.modified and session.get("ronovo_sub"):
            players.store(session["ronovo_sub"], progress(), session.get("saved_at", 0))
        return response
