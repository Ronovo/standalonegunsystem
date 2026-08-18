import random
import unittest

from gunsystem import Catalog, Target, resolve_shot
from gunsystem.combat import apply_range_modifier, apply_size_modifier, apply_spray, compute_damage


class SequenceRng(random.Random):
    def __init__(self, values):
        super().__init__()
        self._values = list(values)
        self._index = 0

    def randint(self, a, b):
        value = self._values[self._index]
        self._index += 1
        return value


class CombatMathTests(unittest.TestCase):
    def test_close_range_bonus_uses_50m_bands(self):
        self.assertEqual(apply_range_modifier(51, 100, False, 50), 50)
        self.assertEqual(apply_range_modifier(50, 100, False, 50), 45)
        self.assertEqual(apply_range_modifier(49, 100, False, 50), 45)

    def test_far_range_penalty(self):
        self.assertEqual(apply_range_modifier(150, 100, False, 50), 60)
        self.assertEqual(apply_range_modifier(100, 100, False, 50), 50)

    def test_sniper_close_bonus_is_capped(self):
        self.assertEqual(apply_range_modifier(0, 500, True, 80), 60)

    def test_size_modifiers(self):
        self.assertAlmostEqual(apply_size_modifier("s", 100), 110)
        self.assertAlmostEqual(apply_size_modifier("l", 100), 90)
        self.assertEqual(apply_size_modifier("m", 100), 100)

    def test_spray_tiers(self):
        self.assertEqual(apply_spray(10, 1), 10)
        self.assertAlmostEqual(apply_spray(10, 2), 12)
        self.assertAlmostEqual(apply_spray(10, 3), 12)
        self.assertAlmostEqual(apply_spray(10, 4), 15)
        self.assertAlmostEqual(apply_spray(10, 7), 15)
        self.assertAlmostEqual(apply_spray(10, 8), 20)
        self.assertAlmostEqual(apply_spray(10, 11), 50)
        self.assertAlmostEqual(apply_spray(10, 31), 100)

    def test_damage_falls_off_and_clamps_at_zero(self):
        self.assertEqual(compute_damage(100, 100, 50), 50)
        self.assertEqual(compute_damage(150, 100, 50), 25)
        self.assertEqual(compute_damage(400, 100, 50), 0)


class ResolveShotTests(unittest.TestCase):
    def test_sniper_deals_damage_at_max_range(self):
        gun = Catalog.create("M40A3")
        gun.reload()
        result = resolve_shot(gun, Target(500, "m"), shots_in_string=1, rng=SequenceRng([1, 200]))
        self.assertTrue(result.hit)
        self.assertEqual(result.damage, 100)
        self.assertFalse(result.critical)

    def test_beyond_max_range_is_a_miss(self):
        gun = Catalog.create("M40A3")
        gun.reload()
        result = resolve_shot(gun, Target(501, "m"), shots_in_string=1, rng=SequenceRng([1]))
        self.assertFalse(result.hit)
        self.assertEqual(result.damage, 0)
        self.assertEqual(result.remaining_ammo, 4)

    def test_damage_at_long_range_clamps_to_zero_on_hit(self):
        gun = Catalog.create("M16A4")
        gun.reload()
        result = resolve_shot(gun, Target(450, "m"), shots_in_string=1, rng=SequenceRng([1, 200]))
        self.assertTrue(result.hit)
        self.assertEqual(result.damage, 0)

    def test_empty_weapon_cannot_fire(self):
        gun = Catalog.create("Barrett .50Cal")
        first = resolve_shot(gun, Target(50, "m"), rng=SequenceRng([1, 200]))
        self.assertFalse(first.hit)
        self.assertEqual(first.remaining_ammo, 0)

        gun.reload()
        live = resolve_shot(gun, Target(50, "m"), rng=SequenceRng([1, 200]))
        empty = resolve_shot(gun, Target(50, "m"), rng=SequenceRng([1, 200]))
        self.assertTrue(live.hit)
        self.assertFalse(empty.hit)
        self.assertEqual(empty.remaining_ammo, 0)
        self.assertEqual(gun.current_ammo, 0)


if __name__ == "__main__":
    unittest.main()
