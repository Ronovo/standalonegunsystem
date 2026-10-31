import time

from flask import session

from gunsystem import Catalog, FireMode, ReloadStep, hit_chance
from gunsystem.dummy import RANGES, Dummy
from gunsystem.simulation import pull_trigger
from gunsystem.target import SIZES

LOG_LENGTH = 6
FIRE_LABELS = {FireMode.SINGLE: "a shot", FireMode.BURST: "a 3 round burst", FireMode.AUTO: "a string"}


class RangeSession:
    """Range state for one browser, rebuilt from and saved to the signed Flask session cookie."""

    def __init__(self, state: dict):
        self.state = state
        self.weapon = Catalog.create(state["weapon"])
        self.weapon.current_ammo = state["ammo"]
        self.dummy = Dummy(state["size"], state["distance"])
        self.dummy.health = state["health"]
        if FireMode(state["mode"]) not in self.weapon.fire_modes:
            raise ValueError("fire mode not on this weapon")

    @classmethod
    def load(cls) -> "RangeSession | None":
        state = session.get("range")
        if not state:
            return None
        try:
            return cls(dict(state))
        except (KeyError, ValueError, TypeError):
            session.pop("range", None)
            return None

    @classmethod
    def start(cls, weapon_name: str, size: str, distance: int) -> "RangeSession":
        weapon = Catalog.create(weapon_name)
        dummy = Dummy(size, distance)
        return cls(
            {
                "weapon": weapon.name,
                "ammo": weapon.max_ammo,
                "mode": weapon.fire_modes[0].value,
                "reloading": False,
                "size": dummy.size,
                "distance": dummy.distance,
                "health": dummy.max_health,
                "log": [],
                "pulls": 0,
                "rounds": min(weapon.rounds_per_pull, weapon.max_ammo),
            }
        )

    def save(self) -> None:
        self.state.update(
            weapon=self.weapon.name,
            ammo=self.weapon.current_ammo,
            size=self.dummy.size,
            distance=self.dummy.distance,
            health=self.dummy.health,
        )
        session.permanent = True
        session["range"] = self.state
        session["saved_at"] = time.time()

    @property
    def fire_mode(self) -> FireMode:
        return FireMode(self.state["mode"])

    @property
    def fire_label(self) -> str:
        return FIRE_LABELS[self.fire_mode]

    def hit_chance(self) -> float:
        """The chance the first shot of a pull lands on the dummy as it stands."""
        return hit_chance(self.weapon, self.dummy)

    def dummy_far(self) -> float:
        """How far down the lane the dummy stands, 0 at the nearest range and 1 at the farthest."""
        return (self.dummy.distance - RANGES[0]) / (RANGES[-1] - RANGES[0])

    def dummy_height(self) -> int:
        return round(SIZES[self.dummy.size].height * (1 - 0.55 * self.dummy_far()))

    def to_dict(self) -> dict:
        """What the live range page needs to play a pull and keep its readouts right."""
        step = self.reload_step()
        return {
            "weapon": {
                "name": self.weapon.name,
                "ammo": self.weapon.current_ammo,
                "max_ammo": self.weapon.max_ammo,
                "pellets": self.weapon.pellets,
                "mode": self.fire_mode.value,
                "rounds": self.state["rounds"],
                "reload_step": step.label if step else None,
                "reload_seconds": self.weapon.reload_seconds,
            },
            "dummy": {
                "size": self.dummy.size,
                "distance": self.dummy.distance,
                "health": max(self.dummy.health, 0),
                "max_health": self.dummy.max_health,
                "destroyed": self.dummy.is_destroyed(),
                "height": self.dummy_height(),
            },
            "hit_chance": self.hit_chance(),
            "pulls": self.state["pulls"],
            "last_pull": self.state["log"][0] if self.state["log"] else None,
            "destroyed": session.get("destroyed", 0),
        }

    def equip(self, weapon_name: str) -> None:
        self.weapon = Catalog.create(weapon_name)
        self.weapon.reload()
        self.state.update(
            mode=self.weapon.fire_modes[0].value,
            reloading=False,
            rounds=min(self.weapon.rounds_per_pull, self.weapon.max_ammo),
        )

    def new_dummy(self, size: str) -> None:
        self.dummy = Dummy(size, self.dummy.distance)

    def set_fire_mode(self, value: str) -> bool:
        modes = self.weapon.fire_modes
        if value == "next":
            mode = modes[(modes.index(self.fire_mode) + 1) % len(modes)]
        else:
            try:
                mode = FireMode(value)
            except ValueError:
                return False
            if mode not in modes:
                return False
        self.state["mode"] = mode.value
        return True

    def fire(self, requested: int) -> str | None:
        """Pull the trigger once. Returns a message when the shot could not be taken."""
        if self.dummy.is_destroyed():
            return "The dummy is already destroyed. Set up a new one."
        if self.weapon.current_ammo == 0:
            return "Out of Ammo! Try Reloading."
        requested = min(max(requested, 1), self.weapon.max_ammo)
        if self.fire_mode is FireMode.AUTO:
            self.state["rounds"] = requested
        shots = pull_trigger(self.weapon, self.dummy, self.fire_mode, requested)
        self.state["reloading"] = False
        self.state["pulls"] += 1
        entry = {
            "mode": self.fire_mode.display_name,
            "distance": self.dummy.distance,
            "marks": "".join("*" if r.critical else "+" if r.hit else "-" for r, _ in shots),
            "hits": sum(r.hit for r, _ in shots),
            "damage": sum(r.damage for r, _ in shots),
            "pellets": self.weapon.pellets,
            "shots": [[r.damage, max(health, 0), r.pellets_hit] for r, health in shots],
        }
        older = [{key: value for key, value in e.items() if key != "shots"} for e in self.state["log"]]
        self.state["log"] = [entry] + older[: LOG_LENGTH - 1]
        if self.dummy.is_destroyed():
            session["destroyed"] = session.get("destroyed", 0) + 1
        return None

    def reload_step(self) -> ReloadStep | None:
        """The next reload action, or None when the weapon is full."""
        return self.weapon.next_reload_step(self.state["reloading"])

    def reload(self) -> str:
        step = self.reload_step()
        if step is None:
            return "Ammo already full. No need to reload."
        message = self.weapon.take_reload_step(step)
        self.state["reloading"] = step is not ReloadStep.MAGAZINE and self.weapon.current_ammo < self.weapon.max_ammo
        return message
