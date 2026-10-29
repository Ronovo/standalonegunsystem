import os

from flask import Flask, redirect, session, url_for

from ronovo_portfolio_auth import portfolio_sso

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
    if portfolio_sso.enabled():
        add_portfolio_login(app)
    return app


def add_portfolio_login(app: Flask) -> None:
    """The range and destroyed count live in the browser's session cookie. While logged in with a portfolio
    account they are also kept for it; logging in on another browser takes whichever range is newer and the
    higher destroyed count."""
    os.makedirs(app.config["DATA_DIR"], exist_ok=True)
    players = Players(os.path.join(app.config["DATA_DIR"], "players.db"))

    def progress():
        return {key: session.get(key) for key in PROGRESS_KEYS}

    def portfolio_login(account):
        # Progress this browser kept for a different account stays with that account instead of being
        # saved into this one. Progress made before any login has no owner and joins this account.
        if session.get("progress_owner", account["sub"]) != account["sub"]:
            for key in (*PROGRESS_KEYS, "saved_at"):
                session.pop(key, None)
        session["progress_owner"] = account["sub"]
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
        session["portfolio_sub"] = account["sub"]
        session["portfolio_user"] = account["username"]
        players.store(account["sub"], progress(), session.get("saved_at", 0))
        return redirect(url_for("main.menu"))

    portfolio_sso.add_flask_routes(app, "gunsystem", portfolio_login)

    @app.post("/logout")
    def logout():
        session.pop("portfolio_sub", None)
        session.pop("portfolio_user", None)
        return redirect(url_for("main.menu"))

    @app.context_processor
    def inject_portfolio():
        return {"portfolio": True, "portfolio_url": portfolio_sso.portfolio_url()}

    @app.after_request
    def save_progress(response):
        if session.modified and session.get("portfolio_sub"):
            players.store(session["portfolio_sub"], progress(), session.get("saved_at", 0))
        return response
