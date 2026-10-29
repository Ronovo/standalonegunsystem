import unittest
from unittest import mock

from gunsystem import Catalog
from gunsystem.simulation import MAX_BULK_SHOTS, balance_runs
from tests.helpers import make_app


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
        with mock.patch("random.Random.randint", return_value=1):
            self.client.post("/range/fire")
        page = self.client.get("/range").get_data(as_text=True)
        self.assertIn("DUMMY DESTROYED", page)
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

    def test_bulk_report(self):
        response = self.client.get("/bulk/MP5", query_string={"shots": 65, "size": "m", "distance": 100, "mode": "fa"})
        page = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("BREAKDOWN BY MAGAZINE", page)
        self.assertIn("<th>65</th>", page)

    def test_bulk_report_is_capped(self):
        page = self.client.get("/bulk/MP5", query_string={"shots": 10 ** 9}).get_data(as_text=True)
        self.assertIn(f"<th>{MAX_BULK_SHOTS}</th>", page)

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
        self.assertEqual(page.count('<details class="result">'), 1)
        self.assertEqual(page.count("<td>3</td>"), 1)
        self.assertNotIn("<td>4</td>", page)

    def test_results_paginate_and_ignore_bad_filters(self):
        self.run_small_balance()
        page = self.client.get("/balance/results", query_string={"weapon": "Nope", "range": 7}).get_data(as_text=True)
        self.assertIn("OF 945", page)
        self.assertEqual(page.count('<details class="result">'), 50)
        self.assertIn('href="/balance/results?page=2"', page)
        last = self.client.get("/balance/results", query_string={"page": 99}).get_data(as_text=True)
        self.assertIn("Page 19 of 19", last)
        self.assertIn("901-945 OF 945", last)


if __name__ == "__main__":
    unittest.main()
