import time
from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

from gunsystem import Catalog, FireMode, ReloadStyle, Weapon

from demo.dummy import RANGES, SIZE_LABELS, SIZE_STATS, Dummy
from demo.screens.balance import REPORT_DIR, write_report
from demo.simulation import MAGAZINES_PER_RANGE, MagazineResult, balance_runs, combine, run_bulk
from webapp.range_session import RELOAD_LABELS, RangeSession

bp = Blueprint("main", __name__)

MAX_BULK_SHOTS = 1000
RESULTS_PER_PAGE = 50
BALANCE_METRICS = {"accuracy": "Accuracy", "destroyed": "Dummies destroyed", "damage": "Damage"}
RELOAD_NOTES = {
    ReloadStyle.MAGAZINE: "Magazine fed: reloads in one go.",
    ReloadStyle.SHELL: "Tube fed: shells are loaded one at a time.",
    ReloadStyle.REVOLVER: "Revolver: empty the cylinder, then load rounds one at a time.",
}
FIRE_LABELS = {FireMode.SINGLE: "a shot", FireMode.BURST: "a 3 round burst", FireMode.AUTO: "a string"}
DUMMY_HEIGHTS = {"s": 110, "m": 150, "l": 190}


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


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _weapon_or_404(name: str) -> Weapon:
    try:
        return Catalog.create(name)
    except KeyError:
        abort(404)


def _weapons_by_class(category: str | None = None) -> dict[str, list[Weapon]]:
    groups: dict[str, list[Weapon]] = {}
    for weapon in Catalog.all():
        if category is None or weapon.weapon_type.category == category:
            groups.setdefault(weapon.weapon_type.class_name, []).append(weapon)
    return groups


def _size(value) -> str:
    return value if value in SIZE_STATS else "m"


def _distance(value) -> int:
    distance = _int(value, RANGES[0])
    return distance if distance in RANGES else RANGES[0]


def _dummy_height(dummy: Dummy) -> int:
    far = (dummy.distance - RANGES[0]) / RANGES[-1]
    return round(DUMMY_HEIGHTS[dummy.size] * (1 - 0.55 * far))


@bp.get("/")
def menu():
    return render_template("menu.html", destroyed=session.get("destroyed", 0))


@bp.get("/armory")
def armory():
    categories = [
        (category, [f"{name} ({len(weapons)})" for name, weapons in _weapons_by_class(category).items()])
        for category in Catalog.CATEGORIES
    ]
    return render_template("armory.html", categories=categories)


@bp.get("/armory/category/<category>")
def armory_category(category: str):
    if category not in Catalog.CATEGORIES:
        abort(404)
    return render_template("armory_category.html", category=category, groups=_weapons_by_class(category))


@bp.get("/armory/weapon/<name>")
def weapon_detail(name: str):
    weapon = _weapon_or_404(name)
    return render_template(
        "weapon.html", weapon=weapon, stat_max=STAT_MAX, reload_note=RELOAD_NOTES[weapon.reload_style]
    )


def range_action(view):
    """Load the range session, run the action, save, and redirect back to the range."""

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
        reload_label=RELOAD_LABELS.get(step) if step else None,
        reload_note=RELOAD_NOTES[range_session.weapon.reload_style],
        log=range_session.state["log"],
        destroyed=session.get("destroyed", 0),
        sizes=SIZE_STATS,
        ranges=RANGES,
    )


@bp.route("/range/setup", methods=["GET", "POST"])
def range_setup():
    if request.method == "POST":
        weapon = _weapon_or_404(request.form.get("weapon", ""))
        size = _size(request.form.get("size"))
        RangeSession.start(weapon.name, size, _distance(request.form.get("distance"))).save()
        return redirect(url_for(".range_view"))

    current = RangeSession.load()
    return render_template(
        "range_setup.html",
        groups=_weapons_by_class(),
        selected=request.args.get("weapon") or (current.weapon.name if current else None),
        size=current.dummy.size if current else "m",
        distance=current.dummy.distance if current else RANGES[0],
        sizes=SIZE_STATS,
        ranges=RANGES,
        heights=DUMMY_HEIGHTS,
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
        "range_setup.html", groups=_weapons_by_class(), selected=range_session.weapon.name, switching=True
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
    rs.new_dummy(_size(request.form.get("size")))
    return f"New {rs.dummy.size_label.lower()} dummy set up at {rs.dummy.distance} m."


@bp.post("/range/leave")
def range_leave():
    session.pop("range", None)
    return redirect(url_for(".menu"))


@bp.get("/bulk")
def bulk():
    return render_template("bulk.html", groups=_weapons_by_class())


@bp.get("/bulk/<name>")
def bulk_form(name: str):
    weapon = _weapon_or_404(name)
    args = request.args
    modes = {mode.value: mode for mode in weapon.fire_modes}
    values = {
        "shots": min(max(_int(args.get("shots"), weapon.max_ammo), 1), MAX_BULK_SHOTS),
        "size": _size(args.get("size")),
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
        sizes=SIZE_STATS,
        ranges=RANGES,
    )


@bp.get("/balance")
def balance():
    run = current_app.extensions.get("balance_run")
    size = request.args.get("size") if request.args.get("size") in SIZE_LABELS else "Medium"
    metric = request.args.get("metric") if request.args.get("metric") in BALANCE_METRICS else "accuracy"
    rows = [row for row in run["rows"] if row["size"] == size] if run else None
    return render_template(
        "balance.html",
        run=run,
        rows=rows,
        size=size,
        metric=metric,
        sizes=SIZE_LABELS,
        metrics=BALANCE_METRICS,
        ranges=RANGES,
        magazines=MAGAZINES_PER_RANGE,
        report_dir=REPORT_DIR,
    )


@bp.post("/balance")
def balance_run():
    write_files = request.form.get("write_files") == "on"
    started = time.perf_counter()
    rows = []
    for weapon, fire_mode, size_label, ranges in balance_runs():
        if write_files:
            write_report(weapon, fire_mode, size_label, ranges)
        rows.append(
            {
                "group": weapon.weapon_type.class_name,
                "weapon": weapon.name,
                "mode": fire_mode.display_name,
                "size": size_label,
                "ranges": [
                    {"distance": distance, "magazines": magazines, "total": combine(magazines)}
                    for distance, magazines in ranges
                ],
            }
        )
    current_app.extensions["balance_run"] = {
        "rows": rows,
        "finished": time.strftime("%H:%M:%S"),
        "seconds": round(time.perf_counter() - started, 1),
    }
    flash("Report finished." + (f" Text reports saved to {REPORT_DIR}/." if write_files else ""))
    return redirect(url_for(".balance", **request.args))


@bp.get("/balance/results")
def balance_results():
    run = current_app.extensions.get("balance_run")
    args = request.args
    distance = _int(args.get("range"), None)
    filters = {
        "weapon": args.get("weapon") if args.get("weapon") in {w.name for w in Catalog.all()} else None,
        "range": distance if distance in RANGES else None,
        "size": args.get("size") if args.get("size") in SIZE_LABELS else None,
    }
    entries = []
    if run:
        entries = [
            {**{key: row[key] for key in ("group", "weapon", "mode", "size")}, **cell}
            for row in run["rows"]
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
        run=run,
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
        groups=_weapons_by_class(),
        sizes=SIZE_LABELS,
        ranges=RANGES,
        magazines=MAGAZINES_PER_RANGE,
    )
