import threading
import time
from collections import OrderedDict
from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

from gunsystem import Catalog, FireMode, ReloadStyle, Weapon
from gunsystem.dummy import RANGES, Dummy, size_code
from gunsystem.simulation import (
    MAGAZINES_PER_RANGE,
    MAX_BULK_SHOTS,
    REPORT_DIR,
    MagazineResult,
    balance_runs,
    combine,
    run_bulk,
    write_report,
)
from gunsystem.target import SIZES
from webapp.range_session import RangeSession

bp = Blueprint("main", __name__)

RESULTS_PER_PAGE = 50
# Balance results are kept for this many accounts, dropping the one that ran a report longest ago.
MAX_BALANCE_RESULTS = 20
BALANCE_METRICS = {"accuracy": "Accuracy", "destroyed": "Dummies destroyed", "damage": "Damage"}
RELOAD_NOTES = {
    ReloadStyle.MAGAZINE: "Magazine fed: reloads in one go.",
    ReloadStyle.SHELL: "Tube fed: shells are loaded one at a time.",
    ReloadStyle.REVOLVER: "Revolver: empty the cylinder, then load rounds one at a time.",
}
FIRE_LABELS = {FireMode.SINGLE: "a shot", FireMode.BURST: "a 3 round burst", FireMode.AUTO: "a string"}
# A balance run takes a few seconds of CPU, so only one runs at a time.
_balance_lock = threading.Lock()


def _stat_max() -> dict[str, int]:
    weapons = Catalog.all()
    return {
        "damage": max(w.damage for w in weapons),
        "base_accuracy": 100,
        "range": max(w.max_range for w in weapons),
        "max_ammo": max(w.max_ammo for w in weapons),
    }


STAT_MAX = _stat_max()


@bp.app_template_filter("bar")
def text_bar(value: int, maximum: int, width: int = 20) -> str:
    filled = round(max(0, min(value, maximum)) / maximum * width) if maximum else 0
    return "█" * filled + "░" * (width - filled)


@bp.app_template_filter("accuracy_class")
def accuracy_class(result: MagazineResult) -> str:
    if result.hits == 0:
        return "acc-zero"
    if result.accuracy < 50:
        return "acc-low"
    if result.accuracy < 80:
        return "acc-mid"
    return "acc-high"


def _int(value, default: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _weapon_or_404(name: str) -> Weapon:
    try:
        return Catalog.create(name)
    except KeyError:
        abort(404)


def _balance_owner() -> str | None:
    """Whose balance results to use: the logged-in portfolio account, or one shared slot when portfolio login is
    off. None when portfolio login is on but nobody is logged in."""
    if not current_app.extensions.get("portfolio_login"):
        return "local"
    return session.get("portfolio_sub")


def _balance_results() -> OrderedDict:
    return current_app.extensions.setdefault("balance_results", OrderedDict())


def _stored_balance() -> dict | None:
    owner = _balance_owner()
    return _balance_results().get(owner) if owner else None


def _keep_balance(owner: str, report: dict) -> None:
    results = _balance_results()
    results[owner] = report
    results.move_to_end(owner)
    while len(results) > MAX_BALANCE_RESULTS:
        results.popitem(last=False)


def _balance_args() -> dict:
    """The balance page's own query arguments, to carry over a redirect."""
    return {key: request.args[key] for key in ("size", "metric") if key in request.args}


def _distance(value) -> int:
    distance = _int(value, RANGES[0])
    return distance if distance in RANGES else RANGES[0]


def _dummy_height(dummy: Dummy) -> int:
    far = (dummy.distance - RANGES[0]) / (RANGES[-1] - RANGES[0])
    return round(SIZES[dummy.size].height * (1 - 0.55 * far))


@bp.get("/")
def menu():
    return render_template("menu.html", destroyed=session.get("destroyed", 0))


@bp.get("/armory")
def armory():
    categories = [
        (category, [f"{name} ({len(weapons)})" for name, weapons in Catalog.by_class(category).items()])
        for category in Catalog.CATEGORIES
    ]
    return render_template("armory.html", categories=categories)


@bp.get("/armory/category/<category>")
def armory_category(category: str):
    if category not in Catalog.CATEGORIES:
        abort(404)
    return render_template("armory_category.html", category=category, groups=Catalog.by_class(category))


@bp.get("/armory/weapon/<name>")
def weapon_detail(name: str):
    weapon = _weapon_or_404(name)
    return render_template(
        "weapon.html", weapon=weapon, stat_max=STAT_MAX, reload_note=RELOAD_NOTES[weapon.reload_style]
    )


def range_action(view):

    @wraps(view)
    def wrapper():
        range_session = RangeSession.load()
        if range_session is None:
            return redirect(url_for(".range_setup"))
        message = view(range_session)
        range_session.save()
        if message:
            flash(message)
        return redirect(url_for(".range_view"))

    return wrapper


@bp.get("/range")
def range_view():
    range_session = RangeSession.load()
    if range_session is None:
        return redirect(url_for(".range_setup"))
    step = range_session.reload_step()
    return render_template(
        "range.html",
        rs=range_session,
        weapon=range_session.weapon,
        dummy=range_session.dummy,
        dummy_height=_dummy_height(range_session.dummy),
        fire_label=FIRE_LABELS[range_session.fire_mode],
        reload_label=step.label if step else None,
        reload_note=RELOAD_NOTES[range_session.weapon.reload_style],
        log=range_session.state["log"],
        destroyed=session.get("destroyed", 0),
        sizes=SIZES,
        ranges=RANGES,
    )


@bp.route("/range/setup", methods=["GET", "POST"])
def range_setup():
    if request.method == "POST":
        weapon = _weapon_or_404(request.form.get("weapon", ""))
        size = size_code(request.form.get("size"))
        RangeSession.start(weapon.name, size, _distance(request.form.get("distance"))).save()
        return redirect(url_for(".range_view"))

    current = RangeSession.load()
    return render_template(
        "range_setup.html",
        groups=Catalog.by_class(),
        selected=request.args.get("weapon") or (current.weapon.name if current else None),
        size=current.dummy.size if current else "m",
        distance=current.dummy.distance if current else RANGES[0],
        sizes=SIZES,
        ranges=RANGES,
        switching=False,
    )


@bp.route("/range/weapon", methods=["GET", "POST"])
def range_weapon():
    range_session = RangeSession.load()
    if range_session is None:
        return redirect(url_for(".range_setup"))
    if request.method == "POST":
        weapon = _weapon_or_404(request.form.get("weapon", ""))
        range_session.equip(weapon.name)
        range_session.save()
        flash(f"Switched to the {weapon.name}.")
        return redirect(url_for(".range_view"))
    return render_template(
        "range_setup.html", groups=Catalog.by_class(), selected=range_session.weapon.name, switching=True
    )


@bp.post("/range/fire")
@range_action
def range_fire(rs: RangeSession):
    return rs.fire(_int(request.form.get("rounds"), 1))


@bp.post("/range/mode")
@range_action
def range_mode(rs: RangeSession):
    if rs.set_fire_mode(request.form.get("mode", "")):
        return "Fire mode is now " + rs.fire_mode.display_name
    return "That fire mode is not available on this weapon."


@bp.post("/range/distance")
@range_action
def range_distance(rs: RangeSession):
    rs.dummy.distance = _distance(request.form.get("distance"))
    return f"Dummy has been set to range of {rs.dummy.distance}"


@bp.post("/range/reload")
@range_action
def range_reload(rs: RangeSession):
    return rs.reload()


@bp.post("/range/dummy")
@range_action
def range_new_dummy(rs: RangeSession):
    if not rs.dummy.is_destroyed():
        return "Finish off the current dummy first."
    rs.new_dummy(size_code(request.form.get("size")))
    return f"New {rs.dummy.size_label.lower()} dummy set up at {rs.dummy.distance} m."


@bp.post("/range/leave")
def range_leave():
    session.pop("range", None)
    session["saved_at"] = time.time()
    return redirect(url_for(".menu"))


@bp.get("/bulk")
def bulk():
    return render_template("bulk.html", groups=Catalog.by_class())


@bp.get("/bulk/<name>")
def bulk_form(name: str):
    weapon = _weapon_or_404(name)
    args = request.args
    modes = {mode.value: mode for mode in weapon.fire_modes}
    values = {
        "shots": min(max(_int(args.get("shots"), weapon.max_ammo), 1), MAX_BULK_SHOTS),
        "size": size_code(args.get("size")),
        "distance": _distance(args.get("distance")),
        "mode": modes.get(args.get("mode"), weapon.fire_modes[0]),
    }
    report = None
    if "shots" in args:
        dummy = Dummy(values["size"], values["distance"])
        magazines = run_bulk(weapon, values["shots"], dummy, values["mode"])
        report = {"magazines": magazines, "totals": combine(magazines)}
    return render_template(
        "bulk_form.html",
        weapon=weapon,
        values=values,
        report=report,
        max_shots=MAX_BULK_SHOTS,
        sizes=SIZES,
        ranges=RANGES,
    )


@bp.get("/balance")
def balance():
    report = _stored_balance()
    size = size_code(request.args.get("size"))
    metric = request.args.get("metric") if request.args.get("metric") in BALANCE_METRICS else "accuracy"
    rows = [row for row in report["rows"] if row["size"] == size] if report else None
    return render_template(
        "balance.html",
        run=report,
        rows=rows,
        size=size,
        metric=metric,
        sizes=SIZES,
        metrics=BALANCE_METRICS,
        ranges=RANGES,
        magazines=MAGAZINES_PER_RANGE,
        report_dir=REPORT_DIR,
        can_run=_balance_owner() is not None,
    )


@bp.post("/balance")
def balance_run():
    owner = _balance_owner()
    if owner is None:
        flash("Log in with your portfolio account to run a balance report.")
        return redirect(url_for(".balance", **_balance_args()))
    if not _balance_lock.acquire(blocking=False):
        flash("Another balance report is running. Try again in a few seconds.")
        return redirect(url_for(".balance", **_balance_args()))
    try:
        report = _balance_report(request.form.get("write_files") == "on")
    finally:
        _balance_lock.release()
    _keep_balance(owner, report)
    flash("Report finished." + (f" Text reports saved to {REPORT_DIR}/." if report["wrote_files"] else ""))
    return redirect(url_for(".balance", **_balance_args()))


def _balance_report(write_files: bool) -> dict:
    started = time.perf_counter()
    rows = []
    for weapon, fire_mode, size, ranges in balance_runs():
        if write_files:
            write_report(weapon, fire_mode, size, ranges)
        rows.append(
            {
                "group": weapon.weapon_type.class_name,
                "weapon": weapon.name,
                "mode": fire_mode.display_name,
                "size": size,
                "ranges": [
                    {"distance": distance, "magazines": magazines, "total": combine(magazines)}
                    for distance, magazines in ranges
                ],
            }
        )
    return {
        "rows": rows,
        "finished": time.strftime("%H:%M:%S"),
        "seconds": round(time.perf_counter() - started, 1),
        "wrote_files": write_files,
    }


@bp.get("/balance/results")
def balance_results():
    report = _stored_balance()
    args = request.args
    distance = _int(args.get("range"), None)
    filters = {
        "weapon": args.get("weapon") if args.get("weapon") in Catalog.names() else None,
        "range": distance if distance in RANGES else None,
        "size": args.get("size") if args.get("size") in SIZES else None,
    }
    entries = []
    if report:
        entries = [
            {**{key: row[key] for key in ("group", "weapon", "mode", "size")}, **cell}
            for row in report["rows"]
            if filters["weapon"] in (None, row["weapon"]) and filters["size"] in (None, row["size"])
            for cell in row["ranges"]
            if filters["range"] in (None, cell["distance"])
        ]

    with_hits = [e for e in entries if e["total"].hits]
    pages = max(1, -(-len(entries) // RESULTS_PER_PAGE))
    page = min(max(_int(args.get("page"), 1), 1), pages)
    start = (page - 1) * RESULTS_PER_PAGE
    return render_template(
        "balance_results.html",
        run=report,
        filters=filters,
        summary=combine([e["total"] for e in entries]),
        count=len(entries),
        best=max(with_hits, key=lambda e: e["total"].accuracy, default=None),
        worst=min(with_hits, key=lambda e: e["total"].accuracy, default=None),
        no_hits=len(entries) - len(with_hits),
        page_entries=entries[start : start + RESULTS_PER_PAGE],
        start=start,
        page=page,
        pages=pages,
        groups=Catalog.by_class(),
        sizes=SIZES,
        ranges=RANGES,
        magazines=MAGAZINES_PER_RANGE,
    )
