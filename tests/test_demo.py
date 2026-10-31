import runpy
import unittest
from pathlib import Path
from unittest import mock

from demo import main
from demo.screens import armory, balance, bulk, range as range_screen
from demo.ui import dummies, formatter, weapons
from gunsystem import Catalog, FireMode
from gunsystem.dummy import RANGES, Dummy
from tests.helpers import rolls

BACK_FROM_SMALL_ARMS = str(len(Catalog.names("Small Arms")) + 1)
BACK_FROM_LARGE_ARMS = str(len(Catalog.names("Large Arms")) + 1)


def start(test: unittest.TestCase, patcher):
    value = patcher.start()
    test.addCleanup(patcher.stop)
    return value


class Console:
    """Answers the demo's input() prompts in order and records everything it prints or asks. A test fails when the
    demo asks for more answers than it was given, or leaves some unused."""

    def __init__(self, test: unittest.TestCase, *answers: str):
        self.answers = list(answers)
        self.lines: list[str] = []
        start(test, mock.patch("builtins.input", self.input))
        start(test, mock.patch("builtins.print", self.print))
        start(test, mock.patch("os.system", lambda command: 0))
        test.addCleanup(lambda: test.assertEqual(self.answers, [], "answers the demo never asked for"))

    def input(self, prompt: str = "") -> str:
        self.lines.append(prompt)
        if not self.answers:
            raise AssertionError(f"the demo asked for more input: {prompt!r}")
        return self.answers.pop(0)

    def print(self, *values, sep=" ", end="\n") -> None:
        self.lines.append(sep.join(map(str, values)))

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


class MainMenuTests(unittest.TestCase):
    def test_quit_leaves_straight_away(self):
        console = Console(self, "5")
        main.run()
        self.assertIn("Welcome to Ronovo's Stand Alone Gun System", console.text)
        self.assertEqual(console.text.count("MAIN MENU"), 1)

    def test_a_wrong_pick_says_so_and_shows_the_menu_again(self):
        console = Console(self, "9", "5")
        main.run()
        self.assertEqual(console.text.count("Incorrect choice. Try again."), 1)
        self.assertEqual(console.text.count("MAIN MENU"), 2)

    def test_each_pick_opens_its_screen(self):
        Console(self, "1", "2", "3", "4", "5")
        opened = [start(self, mock.patch.object(armory, "armory_main_menu")),
                  start(self, mock.patch.object(range_screen, "range_main")),
                  start(self, mock.patch.object(bulk, "bulk_shots")),
                  start(self, mock.patch.object(balance, "balance_report"))]
        main.run()
        for screen in opened:
            screen.assert_called_once_with()

    def test_python_dash_m_demo_starts_the_menu(self):
        console = Console(self, "5")
        runpy.run_module("demo", run_name="__main__")
        self.assertIn("MAIN MENU", console.text)


class FormatterTests(unittest.TestCase):
    def test_clear_uses_the_command_for_the_system(self):
        for system, command in (("nt", "cls"), ("posix", "clear")):
            with self.subTest(system=system), mock.patch.object(formatter, "os") as fake_os:
                fake_os.name = system
                formatter.clear()
                fake_os.system.assert_called_once_with(command)

    def test_a_pick_comes_back_counted_from_zero(self):
        console = Console(self, "2")
        self.assertEqual(formatter.choose(["Pistol", "Rifle"]), 1)
        self.assertIn("1.) Pistol\n2.) Rifle\nPick 1-2", console.text)

    def test_the_back_option_is_numbered_last_and_returns_none(self):
        console = Console(self, "3")
        self.assertIsNone(formatter.choose(["Pistol", "Rifle"], back="Back"))
        self.assertIn("3.) Back\nPick 1-3", console.text)

    def test_a_bad_answer_asks_again(self):
        console = Console(self, "rifle", "0", "1")
        self.assertEqual(formatter.choose(["Pistol", "Rifle"], invalid="Nope"), 0)
        self.assertEqual(console.text.count("Nope"), 2)

    def test_without_retry_a_bad_answer_gives_up(self):
        console = Console(self, "3")
        self.assertIsNone(formatter.choose(["Pistol", "Rifle"], invalid="Nope", retry=False))
        self.assertEqual(console.text.count("Nope"), 1)


class WeaponPromptTests(unittest.TestCase):
    def test_picking_a_category_and_weapon_gives_it_loaded(self):
        Console(self, "1", "1")
        weapon = weapons.get_selected_weapon()
        self.assertEqual((weapon.name, weapon.current_ammo), ("M1911", weapon.max_ammo))

    def test_a_bad_category_goes_back_to_the_menu(self):
        console = Console(self, "4")
        self.assertIsNone(weapons.get_selected_weapon())
        self.assertIn("Incorrect choice. Returning to Menu", console.text)

    def test_backing_out_of_the_weapon_list_picks_nothing(self):
        Console(self, "1", BACK_FROM_SMALL_ARMS)
        self.assertIsNone(weapons.get_selected_weapon())

    def test_fire_mode_choices_are_the_weapons_own(self):
        rifle = Catalog.create("M16A4")
        Console(self, "2", "4", "7")
        self.assertIs(weapons.set_fire_mode(rifle), FireMode.BURST)
        self.assertIsNone(weapons.set_fire_mode(rifle))
        self.assertIsNone(weapons.set_fire_mode(rifle))

    def test_a_full_weapon_needs_no_reload(self):
        weapon = Catalog.create("M1911")
        weapon.reload()
        console = Console(self)
        self.assertFalse(weapons.interactive_reload(weapon))
        self.assertIn("Ammo already full", console.text)

    def test_a_magazine_reloads_without_asking(self):
        weapon = Catalog.create("M1911")
        console = Console(self)
        self.assertTrue(weapons.interactive_reload(weapon))
        self.assertEqual(weapon.current_ammo, weapon.max_ammo)
        self.assertIn("Weapon is reloaded!", console.text)
        self.assertNotIn("manually loaded", console.text)

    def test_a_shotgun_asks_before_each_shell(self):
        weapon = Catalog.create("W1200")
        weapon.current_ammo = weapon.max_ammo - 2
        console = Console(self, "", "")
        self.assertTrue(weapons.interactive_reload(weapon))
        self.assertEqual(weapon.current_ammo, weapon.max_ammo)
        self.assertIn("Tube fed: shells are loaded one at a time.", console.text)
        self.assertEqual(console.text.count("Press any button to load a shell"), 2)

    def test_the_armory_shows_stats_without_the_ammo_count(self):
        console = Console(self, "")
        weapons.print_armory_display("M40A3")
        self.assertIn("You have selected M40A3", console.text)
        self.assertIn(Catalog.create("M40A3").describe(), console.text)
        self.assertNotIn("Current Ammo", console.text)

    def test_the_range_shows_the_ammo_left(self):
        weapon = Catalog.create("M40A3")
        weapon.current_ammo = 3
        console = Console(self, "")
        weapons.print_range_display(weapon)
        self.assertIn("Your current weapon is M40A3", console.text)
        self.assertIn("Current Ammo : 3", console.text)


class DummyPromptTests(unittest.TestCase):
    def test_a_new_dummy_takes_a_size_and_a_range(self):
        console = Console(self, "S", "2")
        dummy = dummies.prompt_new_dummy(debug=True)
        self.assertEqual((dummy.size, dummy.distance, dummy.health), ("s", RANGES[1], dummy.max_health))
        self.assertIn(f"Dummy has been set to range of {RANGES[1]}", console.text)

    def test_an_unknown_size_is_medium(self):
        console = Console(self, "huge", "1")
        self.assertEqual(dummies.prompt_new_dummy().size, "m")
        self.assertIn("Invalid Option, Dummy set to Medium", console.text)
        self.assertNotIn("Dummy has been set to range", console.text)

    def test_a_replacement_dummy_keeps_the_range_it_was_given(self):
        Console(self, "l")
        dummy = dummies.prompt_new_dummy(distance=RANGES[3])
        self.assertEqual((dummy.size, dummy.distance), ("l", RANGES[3]))

    def test_going_back_keeps_the_range(self):
        dummy = Dummy("m", RANGES[2])
        console = Console(self, str(len(RANGES) + 1))
        dummies.prompt_dummy_range(dummy, debug=True)
        self.assertEqual(dummy.distance, RANGES[2])
        self.assertNotIn("Dummy has been set to range", console.text)


class ArmoryScreenTests(unittest.TestCase):
    def test_browsing_a_weapon_returns_to_the_list(self):
        console = Console(self, "3", "1", "", BACK_FROM_LARGE_ARMS)
        armory.armory_main_menu()
        self.assertIn("You have selected M40A3", console.text)
        self.assertEqual(console.text.count("Weapons List"), 2)

    def test_a_bad_category_leaves_the_armory(self):
        console = Console(self, "0")
        armory.armory_main_menu()
        self.assertNotIn("Weapons List", console.text)


class BalanceScreenTests(unittest.TestCase):
    def setUp(self):
        self.write_report = mock.Mock()
        start(self, mock.patch.object(balance, "balance_runs", lambda: iter([("first run",), ("second run",)])))
        start(self, mock.patch.object(balance, "write_report", self.write_report))
        start(self, mock.patch.object(balance, "REPORT_DIR", Path("Reports Here")))

    def test_one_stops_before_anything_runs(self):
        Console(self, "1")
        balance.balance_report()
        self.write_report.assert_not_called()

    def test_any_other_answer_writes_every_run(self):
        for answer in ("", "2", "go"):
            with self.subTest(answer=answer):
                self.write_report.reset_mock()
                console = Console(self, answer, "")
                balance.balance_report()
                self.assertEqual(self.write_report.call_args_list, [mock.call("first run"), mock.call("second run")])
                self.assertIn(f"You can find it in the {Path('Reports Here').resolve()} folder.", console.text)


class BulkScreenTests(unittest.TestCase):
    def test_a_bulk_report_fires_the_shots_asked_for(self):
        console = Console(self, "1", "1", "10", "s", "1", "1", "")
        with rolls(hit=True):
            bulk.bulk_shots()
        self.assertIn("You have selected 1 full magazines", console.text)
        self.assertIn("You also have a non-full magazine with 3 in it.", console.text)
        self.assertIn("Magazine 1: 3 Hits / 0 Misses", console.text)
        self.assertIn("Magazine 2: 7 Hits / 0 Misses", console.text)

    def test_backing_out_of_the_weapon_list_skips_the_report(self):
        console = Console(self, "1", BACK_FROM_SMALL_ARMS)
        bulk.bulk_shots()
        self.assertNotIn("How many shots", console.text)

    def test_backing_out_of_the_fire_mode_uses_the_first_mode(self):
        Console(self, "2", "5", "3", "m", "1", "4", "")
        run_bulk = start(self, mock.patch.object(bulk, "run_bulk", wraps=bulk.run_bulk))
        bulk.bulk_shots()
        self.assertIs(run_bulk.call_args.args[3], FireMode.SINGLE)

    def test_a_bad_or_missing_count_fires_one_magazine(self):
        for answer in ("lots", "0"):
            with self.subTest(answer=answer):
                console = Console(self, answer)
                self.assertEqual(bulk.ask_total_shots(7), 0)
                self.assertIn("You have selected 1 full magazines", console.text)
                self.assertNotIn("non-full magazine", console.text)


class RangeScreenTests(unittest.TestCase):
    def setUp(self):
        start(self, mock.patch.object(range_screen, "destroyed_dummy", 0))

    def test_backing_out_of_the_weapon_list_leaves_the_range(self):
        console = Console(self, "1", BACK_FROM_SMALL_ARMS)
        range_screen.range_main()
        self.assertNotIn("SHOOTING MENU", console.text)

    def test_hits_take_health_off_the_dummy(self):
        console = Console(self, "1", "1", "m", "1", "1", "", "", "1", "", "", "7")
        with rolls(hit=True):
            range_screen.range_main()
        self.assertIn("Hit!\nDamage dealt = 50\nDummy health is now 150\n", console.text)
        self.assertIn("Your weapon now has 5 bullets.\nHit!\nDamage dealt = 50\nDummy health is now 100\n",
                      console.text)

    def test_a_miss_and_a_critical(self):
        console = Console(self, "1", "1", "m", "1", "1", "", "", "7")
        with rolls(hit=False):
            range_screen.range_main()
        self.assertIn("Your weapon now has 6 bullets.\nMiss!", console.text)
        console.answers += ["1", "1", "m", "1", "1", "", "", "7"]
        with rolls(hit=True, critical=True):
            range_screen.range_main()
        self.assertIn("Hit!\nCritical hit!\nDamage dealt = 100", console.text)

    def test_an_empty_weapon_does_not_fire(self):
        console = Console(self, "2", "2", "l", "7", *["1", "", ""] * 4, "1", "", "7")
        with rolls(hit=False):
            range_screen.range_main()
        self.assertEqual(console.text.count("Press any key to shoot"), 4)
        self.assertIn("Out of Ammo! Try Reloading", console.text)

    def test_a_shotgun_counts_its_pellets(self):
        console = Console(self, "2", "1", "m", "1", "1", "", "", "7")
        with rolls(hit=True):
            range_screen.range_main()
        self.assertIn("Hit!\n8 of 8 pellets\nDamage dealt = 75\nDummy health is now 125\n", console.text)

    def test_full_auto_fires_the_shots_asked_for(self):
        console = Console(self, "2", "5", "l", "1",
                          "2", "3", "",
                          "1", "5", "", "",
                          "1", "many", "", "",
                          "7")
        with rolls(hit=False):
            range_screen.range_main()
        self.assertIn("Current Fire Mode is Single Shot", console.text)
        self.assertIn("New Fire Mode is Fully Automatic", console.text)
        self.assertIn("Your weapon now has 25 bullets.", console.text)
        self.assertIn("Your weapon now has 24 bullets.", console.text)
        self.assertNotIn("Your weapon now has 23 bullets.", console.text)

    def test_backing_out_of_the_fire_mode_keeps_it(self):
        console = Console(self, "2", "5", "l", "1", "2", "4", "", "7")
        range_screen.range_main()
        self.assertIn("New Fire Mode is Single Shot", console.text)

    def test_moving_the_dummy(self):
        console = Console(self, "1", "1", "m", "1", "3", "4", "", "7")
        range_screen.range_main()
        self.assertIn(f"Dummy has been set to range of {RANGES[3]}", console.text)

    def test_reloading_tops_up_only_a_used_weapon(self):
        console = Console(self, "1", "1", "m", "1", "4", "", "1", "", "", "4", "", "7")
        with rolls(hit=False):
            range_screen.range_main()
        self.assertIn("Ammo before reload is : 7\nAmmo already full", console.text)
        self.assertIn("Ammo before reload is : 6", console.text)
        self.assertIn("Current Ammo is : 7", console.text)

    def test_weapon_info_and_a_wrong_pick(self):
        console = Console(self, "1", "1", "m", "1", "5", "", "", "8", "", "7")
        range_screen.range_main()
        self.assertIn("Your current weapon is M1911", console.text)
        self.assertIn("Incorrect choice. Try again.", console.text)

    def test_switching_weapons_resets_the_fire_mode(self):
        console = Console(self, "2", "5", "m", "1",
                          "2", "3", "",
                          "6", "1", BACK_FROM_SMALL_ARMS, "",
                          "2", "4", "",
                          "6", "1", "5", "",
                          "2", "3", "",
                          "5", "", "",
                          "7")
        range_screen.range_main()
        self.assertEqual(console.text.count("Current Fire Mode is Fully Automatic"), 1)
        self.assertEqual(console.text.count("Current Fire Mode is Single Shot"), 2)
        self.assertIn("Your current weapon is Glock 18", console.text)

    def test_destroyed_dummies_are_counted_and_replaced(self):
        console = Console(self, "3", "3", "s", "1",
                          "1", "", "", "1", "m",
                          "4", "",
                          "1", "", "", "2")
        with rolls(hit=True):
            range_screen.range_main()
        self.assertIn("DUMMY DESTROYED!\nYou have destroyed 1 dummies.", console.text)
        self.assertIn("DUMMY DESTROYED!\nYou have destroyed 2 dummies.", console.text)
        self.assertEqual(range_screen.destroyed_dummy, 2)

    def test_an_overkill_shot_reads_as_zero_health(self):
        console = Console(self, "3", "3", "s", "1", "1", "", "", "2")
        with rolls(hit=True):
            range_screen.range_main()
        self.assertIn("Dummy health is now 0\n", console.text)


if __name__ == "__main__":
    unittest.main()
