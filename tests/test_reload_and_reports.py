import os
import tempfile
import unittest
from unittest import mock

import gunsystem.simulation
from gunsystem.dummy import Dummy
from gunsystem.simulation import run_magazines, write_report
from demo.ui.weapons import interactive_reload
from gunsystem import Catalog, FireMode, ReloadStyle
from tests.test_portfolio_login import PUBLIC_KEY, issue
from webapp import create_app
from webapp import views


class ReloadStepTests(unittest.TestCase):
    def test_magazine_reloads_in_one_step(self):
        weapon = Catalog.create("M1911")
        weapon.current_ammo = 1
        self.assertIs(weapon.next_reload_step(), ReloadStyle.MAGAZINE)
        weapon.take_reload_step(ReloadStyle.MAGAZINE)
        self.assertIsNone(weapon.next_reload_step())

    def test_revolver_empties_then_loads_one_round_at_a_time(self):
        weapon = Catalog.create(".38 Special")
        weapon.current_ammo = 2
        self.assertEqual(weapon.next_reload_step(), "empty")
        weapon.take_reload_step("empty")
        self.assertEqual(weapon.current_ammo, 0)
        self.assertIs(weapon.next_reload_step(loading=True), ReloadStyle.REVOLVER)
        weapon.take_reload_step(ReloadStyle.REVOLVER)
        self.assertEqual(weapon.current_ammo, 1)

    def test_terminal_reload_uses_the_same_steps(self):
        weapon = Catalog.create(".38 Special")
        weapon.current_ammo = 2
        with mock.patch("builtins.input", return_value=""), mock.patch("builtins.print"):
            self.assertTrue(interactive_reload(weapon))
        self.assertEqual(weapon.current_ammo, weapon.max_ammo)


class ReportFileTests(unittest.TestCase):
    def test_report_is_written_without_touching_stdout(self):
        weapon = Catalog.create("M1911")
        weapon.reload()
        magazines = run_magazines(weapon, 1, Dummy("Small"), FireMode.SINGLE)
        with tempfile.TemporaryDirectory() as folder, mock.patch.object(gunsystem.simulation, "REPORT_DIR",
                                                                         gunsystem.simulation.Path(folder)):
            write_report(weapon, FireMode.SINGLE, "Small", [(50, magazines)])
            path = os.path.join(folder, weapon.weapon_type.class_name, "M1911", "Small", "Single Shot.txt")
            with open(path, encoding="utf-8") as report:
                text = report.read()
        self.assertTrue(text.startswith("Balance Report for M1911\n" + "-" * 36 + "\n\nResults for 50M\n"))
        self.assertIn("Totals for All Shots", text)


class RangeSessionTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True, "SECRET_KEY": "test"}).test_client()
        self.client.post("/range/setup", data={"weapon": "FN FAL", "size": "s", "distance": "50"})

    def test_a_bad_mode_in_the_cookie_starts_over_instead_of_failing(self):
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "mode": "nonsense"}
        response = self.client.get("/range")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/range/setup"))

    def test_rounds_per_pull_are_capped_at_the_magazine(self):
        with self.client.session_transaction() as session:
            session["range"] = {**session["range"], "mode": FireMode.AUTO.value}
        self.client.post("/range/fire", data={"rounds": "999999"})
        with self.client.session_transaction() as session:
            self.assertEqual(session["range"]["rounds"], Catalog.create("FN FAL").max_ammo)


class BalanceAccessTests(unittest.TestCase):
    def setUp(self):
        data_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(data_dir.cleanup)
        env = mock.patch.dict(os.environ, {"PORTFOLIO_SSO_URL": "http://portfolio.test",
                                           "PORTFOLIO_SSO_PUBLIC_KEY": PUBLIC_KEY})
        env.start()
        self.addCleanup(env.stop)
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test", "DATA_DIR": data_dir.name})
        small = mock.patch.object(views, "balance_runs", lambda: gunsystem.simulation.balance_runs(magazines_per_range=1))
        small.start()
        self.addCleanup(small.stop)

    def logged_in(self, sub):
        client = self.app.test_client()
        location = client.get("/sso/login").location
        state = location.split("state=")[1].split("&")[0]
        client.post("/sso/callback", data={"state": state, "token": issue(sub)})
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

    def test_only_one_run_at_a_time(self):
        client = self.logged_in("1")
        with views._balance_lock:
            page = client.post("/balance", follow_redirects=True).data
        self.assertIn(b"Another balance report is running", page)


if __name__ == "__main__":
    unittest.main()
