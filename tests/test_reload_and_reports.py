import unittest
from unittest import mock

import gunsystem.simulation
from gunsystem import Catalog, FireMode, ReloadStep
from tests.helpers import log_in, make_app
from webapp import views


class ReloadStepTests(unittest.TestCase):
    def test_magazine_reloads_in_one_step(self):
        weapon = Catalog.create("M1911")
        weapon.current_ammo = 1
        self.assertIs(weapon.next_reload_step(), ReloadStep.MAGAZINE)
        self.assertEqual(weapon.take_reload_step(ReloadStep.MAGAZINE), "Weapon is reloaded!")
        self.assertIsNone(weapon.next_reload_step())

    def test_a_full_weapon_takes_no_more_rounds(self):
        weapon = Catalog.create("W1200")
        weapon.reload()
        self.assertFalse(weapon.load_round())
        self.assertEqual(weapon.current_ammo, weapon.max_ammo)

    def test_revolver_empties_then_loads_one_round_at_a_time(self):
        weapon = Catalog.create(".38 Special")
        weapon.current_ammo = 2
        self.assertIs(weapon.next_reload_step(), ReloadStep.EMPTY)
        weapon.take_reload_step(ReloadStep.EMPTY)
        self.assertEqual(weapon.current_ammo, 0)
        self.assertIs(weapon.next_reload_step(loading=True), ReloadStep.ROUND)
        self.assertEqual(weapon.take_reload_step(ReloadStep.ROUND), "One bullet loaded. 5 remaining.")
        self.assertEqual(weapon.current_ammo, 1)


class RangeSessionTests(unittest.TestCase):
    def setUp(self):
        self.client = make_app(self).test_client()
        self.client.post("/range/setup", data={"weapon": "FN FAL", "size": "s", "distance": "50"})

    def test_a_bad_mode_in_the_cookie_starts_over_instead_of_failing(self):
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "mode": "nonsense"}
        response = self.client.get("/range")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/range/setup"))

    def test_a_fire_mode_the_weapon_lacks_starts_over(self):
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "weapon": "M1911", "ammo": 7, "mode": FireMode.AUTO.value}
        response = self.client.get("/range")
        self.assertTrue(response.location.endswith("/range/setup"))
        with self.client.session_transaction() as session:
            self.assertNotIn("range", session)

    def test_rounds_per_pull_are_capped_at_the_magazine(self):
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "mode": FireMode.AUTO.value}
        self.client.post("/range/fire", data={"rounds": "999999"})
        with self.client.session_transaction() as session:
            self.assertEqual(session["range"]["rounds"], Catalog.create("FN FAL").max_ammo)


class BalanceAccessTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app(self, portfolio=True)
        small = mock.patch.object(views, "balance_runs", lambda: gunsystem.simulation.balance_runs(magazines_per_range=1))
        small.start()
        self.addCleanup(small.stop)

    def logged_in(self, sub):
        client = self.app.test_client()
        log_in(client, sub)
        return client

    def test_running_needs_a_login(self):
        client = self.app.test_client()
        self.assertIn(b"Log in with your portfolio account to run", client.get("/balance").data)
        client.post("/balance")
        self.assertIn(b"No balance report has been run yet.", client.get("/balance/results").data)

    def test_each_account_keeps_its_own_results(self):
        first, second = self.logged_in("1"), self.logged_in("2")
        first.post("/balance")
        self.assertNotIn(b"No balance report has been run yet.", first.get("/balance/results").data)
        self.assertIn(b"No balance report has been run yet.", second.get("/balance/results").data)

    def test_results_are_dropped_for_the_account_that_ran_one_longest_ago(self):
        clients = {sub: self.logged_in(sub) for sub in ("1", "2", "3")}
        with mock.patch.object(views, "MAX_BALANCE_RESULTS", 2):
            for sub in ("1", "2", "1", "3"):
                clients[sub].post("/balance")
        has_results = {sub: b"No balance report has been run yet." not in client.get("/balance/results").data
                       for sub, client in clients.items()}
        self.assertEqual(has_results, {"1": True, "2": False, "3": True})

    def test_only_one_run_at_a_time(self):
        client = self.logged_in("1")
        with views._balance_lock:
            page = client.post("/balance", follow_redirects=True).data
        self.assertIn(b"Another balance report is running", page)


if __name__ == "__main__":
    unittest.main()
