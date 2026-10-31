import os
import re
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gunsystem import Catalog
from gunsystem.dummy import RANGES
from gunsystem.simulation import MAX_BULK_SHOTS, balance_runs
from tests.helpers import NO_PORTFOLIO, make_app, rolls
from webapp import create_app, views


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.client = make_app(self).test_client()

    def range_state(self):
        with self.client.session_transaction() as session:
            return dict(session["range"])

    def enter_range(self, weapon="M1911", size="s", distance="50"):
        return self.client.post("/range/setup", data={"weapon": weapon, "size": size, "distance": distance})

    def test_menu_and_armory_pages_render(self):
        for url in ("/", "/armory", "/armory/category/Small Arms", "/armory/weapon/M40A3", "/bulk", "/balance"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_every_weapon_page_renders(self):
        for weapon in Catalog.all():
            with self.subTest(weapon=weapon.name):
                response = self.client.get(f"/armory/weapon/{weapon.name}")
                self.assertEqual(response.status_code, 200)
                self.assertIn(weapon.name, response.get_data(as_text=True))

    def test_unknown_weapon_and_category_are_404(self):
        self.assertEqual(self.client.get("/armory/weapon/Not A Gun").status_code, 404)
        self.assertEqual(self.client.get("/armory/category/Nope").status_code, 404)
        self.assertEqual(self.client.post("/range/setup", data={"weapon": "Not A Gun"}).status_code, 404)

    def test_range_redirects_to_setup_without_a_session(self):
        response = self.client.get("/range")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/range/setup"))
        self.assertEqual(self.client.post("/range/fire").status_code, 302)

    def test_range_setup_fire_and_reload(self):
        self.enter_range()
        state = self.range_state()
        self.assertEqual((state["weapon"], state["ammo"], state["size"], state["distance"]), ("M1911", 7, "s", 50))

        self.client.post("/range/fire")
        state = self.range_state()
        self.assertEqual(state["ammo"], 6)
        self.assertEqual(len(state["log"]), 1)
        self.assertEqual(len(state["log"][0]["marks"]), 1)

        self.client.post("/range/reload")
        self.assertEqual(self.range_state()["ammo"], 7)
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn("SHOOTING MENU", page)
        self.assertIn("Weapon is reloaded!", page)

    def test_every_page_offers_the_themes(self):
        for url in ("/", "/armory", "/range/setup", "/balance"):
            page = self.client.get(url).get_data(as_text=True)
            self.assertIn('<select data-theme-picker>', page, url)
            self.assertIn('<option value="cyberpunk">Cyberpunk</option>', page, url)

    def test_the_range_page_carries_its_state_for_live_fire(self):
        self.enter_range(weapon="MP5", size="m", distance="100")
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn('data-range-mode="live"', page)
        self.assertIn('data-live="fire"', page)
        self.assertIn('<script type="application/json" id="range-state">', page)
        self.assertIn('"pulls": 0', page)

    def test_live_fire_answers_with_the_panels_and_state(self):
        self.enter_range(weapon="W1200", size="m", distance="100")
        with rolls(hit=True):
            response = self.client.post("/range/fire", headers={"Accept": "application/json"})
        data = response.get_json()
        self.assertEqual(set(data), {"html", "state", "message"})
        self.assertIsNone(data["message"])
        self.assertIn("8 of 8 pellets", data["html"])
        state = data["state"]
        self.assertEqual((state["pulls"], state["weapon"]["ammo"], state["last_pull"]["pellets"]), (1, 6, 8))
        self.assertEqual(state["dummy"]["health"], 125)
        data = self.client.post("/range/reload", headers={"Accept": "application/json"}).get_json()
        self.assertEqual(data["message"], "One shell loaded. 0 remaining.")
        self.assertEqual(self.client.get("/range/state").get_json()["weapon"]["ammo"], 7)

    def test_live_fire_is_sent_to_setup_without_a_range(self):
        json = {"Accept": "application/json"}
        self.assertEqual(self.client.post("/range/fire", headers=json).get_json(), {"redirect": "/range/setup"})
        self.assertEqual(self.client.get("/range/state", headers=json).get_json(), {"redirect": "/range/setup"})
        self.assertTrue(self.client.get("/range/state").location.endswith("/range/setup"))

    def test_range_shows_the_hit_chance_for_the_lane(self):
        self.enter_range(weapon="M1911", size="m", distance="100")
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn("80% first shot", page)
        self.client.post("/range/distance", data={"distance": "300"})
        self.assertIn("0% first shot", self.client.get("/range").get_data(as_text=True))

    def test_a_shotgun_log_counts_pellets(self):
        self.enter_range(weapon="W1200", size="l", distance="50")
        with rolls(hit=True):
            self.client.post("/range/fire")
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn("8 of 8 pellets.", page)
        self.assertEqual(self.range_state()["log"][0]["shots"][0][2], 8)

    def test_the_weapon_page_charts_hit_chance_and_damage_per_distance(self):
        page = self.client.get("/armory/weapon/M40A3").get_data(as_text=True)
        self.assertIn("20 rpm", page)
        self.assertIn("HIT CHANCE BY DISTANCE", page)
        self.assertIn("DAMAGE BY DISTANCE", page)
        self.assertEqual(page.count('<span class="caption">500 m</span>'), 2)

    def test_shotgun_damage_per_distance_counts_the_pellets_that_land(self):
        page = self.client.get("/armory/weapon/M1014").get_data(as_text=True)
        damage = re.search(r'DAMAGE BY DISTANCE.*?</section>', page, re.S).group(0)
        self.assertEqual(re.findall(r'<span class="num">(\d+)</span>', damage), ["95", "90", "20", "0", "0", "0", "0"])

    def test_auto_fire_defaults_to_one_second_of_fire(self):
        self.enter_range(weapon="MP5")
        self.assertEqual(self.range_state()["rounds"], 13)
        self.client.post("/range/weapon", data={"weapon": "USAS-12"})
        self.assertEqual(self.range_state()["rounds"], 5)

    def test_rounds_per_pull_follow_the_fire_mode(self):
        self.enter_range(weapon="M16A4")
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn('name="rounds" form="fire-form" value="1" disabled', page)
        self.client.post("/range/mode", data={"mode": "3r"})
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn('name="rounds" form="fire-form" value="3" disabled', page)
        self.client.post("/range/mode", data={"mode": "fa"})
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn('name="rounds" form="fire-form" min="2" max="30" value="13"', page)
        self.client.post("/range/fire", data={"rounds": "1"})
        self.assertEqual(len(self.range_state()["log"][0]["marks"]), 2)

    def test_auto_fire_uses_requested_rounds(self):
        self.enter_range(weapon="M249 SAW", size="l", distance="500")
        self.client.post("/range/mode", data={"mode": "fa"})
        self.client.post("/range/fire", data={"rounds": "12"})
        state = self.range_state()
        self.assertEqual(state["mode"], "fa")
        self.assertEqual(state["ammo"], 88)
        self.assertEqual(len(state["log"][0]["marks"]), 12)

    def test_next_fire_mode_cycles_through_the_weapon_modes(self):
        self.enter_range(weapon="AK47")
        modes = []
        for _ in range(3):
            self.client.post("/range/mode", data={"mode": "next"})
            modes.append(self.range_state()["mode"])
        self.assertEqual(modes, ["3r", "fa", "s"])

    def test_unavailable_fire_mode_is_rejected(self):
        self.enter_range(weapon="M1911")
        self.client.post("/range/mode", data={"mode": "fa"})
        self.assertEqual(self.range_state()["mode"], "s")

    def test_shotgun_loads_one_shell_at_a_time(self):
        self.enter_range(weapon="W1200")
        self.client.post("/range/fire")
        self.client.post("/range/fire")
        self.client.post("/range/reload")
        self.assertEqual(self.range_state()["ammo"], 6)

    def test_revolver_empties_before_loading(self):
        self.enter_range(weapon=".38 Special")
        self.client.post("/range/fire")
        self.client.post("/range/reload")
        self.assertEqual(self.range_state()["ammo"], 0)
        for _ in range(6):
            self.client.post("/range/reload")
        state = self.range_state()
        self.assertEqual(state["ammo"], 6)
        self.assertFalse(state["reloading"])

    def test_destroyed_dummy_counts_and_can_be_replaced(self):
        self.enter_range(weapon="Barrett .50Cal", size="s", distance="500")
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "health": 1}
        with rolls(hit=True):
            self.client.post("/range/fire")
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn("DUMMY DESTROYED", page)
        with self.client.session_transaction() as session:
            self.assertEqual(session["destroyed"], 1)
        page = self.client.post("/range/fire", follow_redirects=True).get_data(as_text=True)
        self.assertIn("The dummy is already destroyed. Set up a new one.", page)
        with self.client.session_transaction() as session:
            self.assertEqual(session["destroyed"], 1)

        self.client.post("/range/dummy", data={"size": "l"})
        state = self.range_state()
        self.assertEqual((state["size"], state["distance"], state["health"]), ("l", 500, 275))

    def test_switch_weapon_keeps_dummy(self):
        self.enter_range(size="l", distance="300")
        self.client.post("/range/weapon", data={"weapon": "AK47"})
        state = self.range_state()
        self.assertEqual((state["weapon"], state["ammo"], state["size"], state["distance"]), ("AK47", 30, "l", 300))

    def test_leave_clears_range(self):
        self.enter_range()
        self.client.post("/range/leave")
        with self.client.session_transaction() as session:
            self.assertNotIn("range", session)

    def test_setup_defaults_to_a_medium_dummy_at_the_nearest_range(self):
        page = self.client.get("/range/setup").get_data(as_text=True)
        self.assertIn('value="m" checked', page)
        self.assertIn(f'value="{RANGES[0]}" checked', page)
        self.assertNotIn("required checked", page)

    def test_setup_starts_from_the_current_range(self):
        self.enter_range(weapon="M40A3", size="l", distance="300")
        page = self.client.get("/range/setup").get_data(as_text=True)
        self.assertIn('value="M40A3" required checked', page)
        self.assertIn('value="l" checked', page)
        self.assertIn('value="300" checked', page)
        page = self.client.get("/range/setup", query_string={"weapon": "AK47"}).get_data(as_text=True)
        self.assertIn('value="AK47" required checked', page)

    def test_setup_picks_guns_by_class_tab(self):
        page = self.client.get("/range/setup").get_data(as_text=True)
        for class_name in Catalog.by_class():
            self.assertIn(f'name="class" value="{class_name}" data-tab', page)
        self.assertIn('value="Pistol" data-tab checked', page)
        self.assertEqual(page.count('name="weapon"'), len(Catalog.names()))
        self.enter_range(weapon="M40A3")
        page = self.client.get("/range/weapon").get_data(as_text=True)
        self.assertIn('value="Sniper" data-tab checked', page)
        self.assertIn('data-gun="m40a3"', page)

    def test_every_gun_has_its_own_drawing(self):
        for name in Catalog.names():
            page = self.client.get(f"/armory/weapon/{name}").get_data(as_text=True)
            self.assertIn(f'data-gun="{views.slug(name)}"', page, name)

    def test_switching_weapons_needs_a_range(self):
        self.assertTrue(self.client.get("/range/weapon").location.endswith("/range/setup"))
        self.assertTrue(self.client.post("/range/weapon", data={"weapon": "AK47"}).location.endswith("/range/setup"))

    def test_the_switch_page_marks_the_weapon_in_hand(self):
        self.enter_range(weapon="G36")
        page = self.client.get("/range/weapon").get_data(as_text=True)
        self.assertIn("SWITCH WEAPONS", page)
        self.assertIn('value="G36" required checked', page)
        self.assertNotIn('name="size"', page)

    def test_moving_the_dummy_keeps_it_in_a_lane(self):
        self.enter_range()
        page = self.client.post("/range/distance", data={"distance": "400"}, follow_redirects=True)
        self.assertIn("Dummy has been set to range of 400", page.get_data(as_text=True))
        self.assertEqual(self.range_state()["distance"], 400)
        self.client.post("/range/distance", data={"distance": "450"})
        self.assertIn(self.range_state()["distance"], RANGES)

    def test_a_standing_dummy_is_not_replaced(self):
        self.enter_range(size="s")
        page = self.client.post("/range/dummy", data={"size": "l"}, follow_redirects=True)
        self.assertIn("Finish off the current dummy first.", page.get_data(as_text=True))
        self.assertEqual(self.range_state()["size"], "s")

    def test_an_unknown_fire_mode_is_rejected(self):
        self.enter_range(weapon="AK47")
        page = self.client.post("/range/mode", data={"mode": "laser"}, follow_redirects=True)
        self.assertIn("That fire mode is not available on this weapon.", page.get_data(as_text=True))
        self.assertEqual(self.range_state()["mode"], "s")

    def test_an_empty_weapon_does_not_fire(self):
        self.enter_range()
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "ammo": 0}
        page = self.client.post("/range/fire", follow_redirects=True)
        self.assertIn("Out of Ammo! Try Reloading.", page.get_data(as_text=True))
        self.assertEqual(self.range_state()["log"], [])

    def test_a_full_weapon_is_not_reloaded(self):
        self.enter_range()
        page = self.client.post("/range/reload", follow_redirects=True)
        self.assertIn("Ammo already full. No need to reload.", page.get_data(as_text=True))

    def test_bulk_report(self):
        response = self.client.get("/bulk/MP5", query_string={"magazines": 3, "size": "m", "distance": 100, "mode": "fa"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("BREAKDOWN BY MAGAZINE", page)
        self.assertIn("<th>90</th>", page)

    def test_bulk_report_is_capped_at_whole_magazines(self):
        page = self.client.get("/bulk/MP5", query_string={"magazines": 10 ** 9}).get_data(as_text=True)
        self.assertIn(f"<th>{MAX_BULK_SHOTS // 30 * 30}</th>", page)

    def test_bulk_form_offers_one_magazine_before_firing(self):
        page = self.client.get("/bulk/MP5").get_data(as_text=True)
        self.assertIn(f'name="magazines" min="1" max="{MAX_BULK_SHOTS // 30}" value="1"', page)
        self.assertIn(">Magazines", page)
        self.assertNotIn("BREAKDOWN BY MAGAZINE", page)

    def test_bulk_form_counts_reloads_for_guns_without_a_magazine(self):
        for name in ("W1200", ".38 Special"):
            self.assertIn(">Reloads", self.client.get(f"/bulk/{name}").get_data(as_text=True), name)
        self.assertIn(">Magazines", self.client.get("/bulk/USAS-12").get_data(as_text=True))

    def test_one_magazine_gives_no_report_by_magazine(self):
        page = self.client.get("/bulk/MP5", query_string={"magazines": 1}).get_data(as_text=True)
        self.assertIn("TOTALS FOR ALL SHOTS", page)
        self.assertIn("Fire more than one magazine to get a report by magazine.", page)
        self.assertNotIn("BREAKDOWN BY MAGAZINE", page)

    def test_balance_report_runs_and_filters(self):
        small_runs = lambda: balance_runs(magazines_per_range=1)
        with mock.patch("webapp.views.balance_runs", small_runs):
            response = self.client.post("/balance", follow_redirects=True)
        page = response.get_data(as_text=True)
        self.assertIn("Report finished.", page)
        self.assertIn("M40A3", page)
        page = self.client.get("/balance", query_string={"size": "l", "metric": "damage"}).get_data(as_text=True)
        self.assertIn('class="chip active" href="/balance?size=l&amp;metric=damage"', page)

    def test_a_balance_run_keeps_only_the_page_arguments(self):
        with mock.patch("webapp.views.balance_runs", lambda: balance_runs(magazines_per_range=1)):
            response = self.client.post("/balance?_method=FOO&size=l")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/balance?size=l"))

    def run_small_balance(self, magazines=2):
        with mock.patch("webapp.views.balance_runs", lambda: balance_runs(magazines_per_range=magazines)):
            self.client.post("/balance")

    def test_results_page_without_a_run(self):
        page = self.client.get("/balance/results").get_data(as_text=True)
        self.assertIn("No balance report has been run yet.", page)

    def test_results_filters_and_magazine_breakdown(self):
        self.run_small_balance(magazines=3)
        page = self.client.get(
            "/balance/results", query_string={"weapon": "M40A3", "range": 500, "size": "s"}
        ).get_data(as_text=True)
        self.assertIn("RESULTS · 1-1 OF 1", page)
        self.assertEqual(page.count('<details class="result"'), 1)
        self.assertEqual(page.count("<td>3</td>"), 1)
        self.assertNotIn("<td>4</td>", page)

    def test_results_paginate_and_ignore_bad_filters(self):
        self.run_small_balance()
        page = self.client.get("/balance/results", query_string={"weapon": "Nope", "range": 7}).get_data(as_text=True)
        self.assertIn("OF 945", page)
        self.assertEqual(page.count('<details class="result"'), 50)
        self.assertIn('href="/balance/results?page=2"', page)
        last = self.client.get("/balance/results", query_string={"page": 99}).get_data(as_text=True)
        self.assertIn("Page 19 of 19", last)
        self.assertIn("901-945 OF 945", last)

    def test_the_coverage_reports_are_served_from_their_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            reports = Path(folder) / "coverage"
            (reports / "python").mkdir(parents=True)
            (reports / "index.html").write_text("landing page", encoding="utf-8")
            (reports / "python" / "index.html").write_text("python report", encoding="utf-8")
            (Path(folder) / "secret.txt").write_text("secret", encoding="utf-8")

            def get(path):
                with self.client.get(path) as response:
                    return response.status_code, response.data

            with mock.patch.object(views, "COVERAGE_DIR", reports):
                self.assertEqual(get("/coverage")[0], 308)
                self.assertEqual(get("/coverage/"), (200, b"landing page"))
                self.assertEqual(get("/coverage/python/"), (200, b"python report"))
                for path in ("/coverage/js/", "/coverage/../secret.txt", "/coverage/%2e%2e/secret.txt"):
                    self.assertEqual(get(path)[0], 404, path)


class AppSettingsTests(unittest.TestCase):
    def setUp(self):
        env = mock.patch.dict(os.environ, NO_PORTFOLIO)
        env.start()
        self.addCleanup(env.stop)

    def test_settings_come_from_the_environment(self):
        settings = {"GUNSYSTEM_SECRET_KEY": "from the shell", "DATA_DIR": "elsewhere", "SECURE_COOKIES": "1"}
        with mock.patch.dict(os.environ, settings):
            app = create_app()
        self.assertEqual((app.config["SECRET_KEY"], app.config["DATA_DIR"], app.config["SESSION_COOKIE_SECURE"]),
                         ("from the shell", "elsewhere", True))

    def test_without_settings_each_start_gets_its_own_key(self):
        with mock.patch.dict(os.environ, {"GUNSYSTEM_SECRET_KEY": "", "SECURE_COOKIES": ""}):
            first, second = create_app(), create_app()
        self.assertNotEqual(first.config["SECRET_KEY"], second.config["SECRET_KEY"])
        self.assertFalse(first.config["SESSION_COOKIE_SECURE"])

    def test_python_dash_m_webapp_serves_the_app(self):
        with mock.patch("flask.Flask.run") as run:
            runpy.run_module("webapp", run_name="__main__")
        run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
