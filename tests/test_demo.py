import unittest

from gunsystem.dummy import Dummy, size_code, size_label
from unittest import mock

import gunsystem.simulation
from gunsystem.simulation import AUTO_ROUNDS_PER_PULL, plan_magazines, run_magazines
from gunsystem import Catalog, FireMode, advance_string, resolve_shot


class MagazinePlanTests(unittest.TestCase):
    def test_partial_magazine_does_not_crash(self):
        count, first = plan_magazines(30, 7)
        self.assertEqual(count, 1)
        self.assertEqual(first, 7)

    def test_exact_magazines(self):
        count, first = plan_magazines(30, 60)
        self.assertEqual(count, 2)
        self.assertEqual(first, 30)

    def test_full_plus_partial(self):
        count, first = plan_magazines(30, 35)
        self.assertEqual(count, 2)
        self.assertEqual(first, 5)


class DummyInstanceTests(unittest.TestCase):
    def test_dummies_do_not_share_health(self):
        small = Dummy("s", distance=50)
        other = Dummy("s", distance=50)
        small.take_damage(125)
        self.assertTrue(small.is_destroyed())
        self.assertEqual(other.health, 125)

    def test_reset_uses_size_health(self):
        large = Dummy("l")
        large.take_damage(50)
        large.reset_health()
        self.assertEqual(large.health, 275)

    def test_sizes_read_as_codes_or_labels(self):
        self.assertEqual((size_code("l"), size_code("Large"), size_code("huge")), ("l", "l", "m"))
        self.assertEqual((size_label("s"), size_label("Small"), size_label(None)), ("Small", "Small", "Medium"))
        self.assertEqual(Dummy("Large").max_health, 275)


class SprayStringTests(unittest.TestCase):
    def test_burst_cycles_every_three_shots(self):
        shots = 0
        sequence = []
        for _ in range(6):
            shots = advance_string(FireMode.BURST, shots)
            sequence.append(shots)
        self.assertEqual(sequence, [1, 2, 3, 1, 2, 3])

    def test_single_stays_at_one(self):
        self.assertEqual(advance_string(FireMode.SINGLE, 0), 1)
        self.assertEqual(advance_string(FireMode.SINGLE, 1), 1)

    def test_auto_increments(self):
        self.assertEqual(advance_string(FireMode.AUTO, 0), 1)
        self.assertEqual(advance_string(FireMode.AUTO, 10), 11)


class ReportFiringTests(unittest.TestCase):
    def test_full_auto_reports_restart_the_string_every_pull(self):
        weapon = next(w for w in Catalog.all() if FireMode.AUTO in w.fire_modes and w.max_ammo > AUTO_ROUNDS_PER_PULL)
        weapon.reload()
        strings = []

        def recording_shot(weapon, dummy, shots_in_string):
            strings.append(shots_in_string)
            return resolve_shot(weapon, dummy, shots_in_string)

        with mock.patch.object(gunsystem.simulation, "resolve_shot", recording_shot):
            run_magazines(weapon, 3, Dummy(), FireMode.AUTO)
        self.assertEqual(len(strings), 3 * weapon.max_ammo)
        self.assertLessEqual(max(strings), AUTO_ROUNDS_PER_PULL)
        self.assertGreater(max(strings), 1)


if __name__ == "__main__":
    unittest.main()
