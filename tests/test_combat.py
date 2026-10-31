import random
import unittest

from gunsystem import Catalog, Target, WeaponType, hit_chance, resolve_shot
from gunsystem.catalog import SNIPER
from gunsystem.combat import (
    MIN_DAMAGE,
    apply_cover_modifier,
    apply_range_modifier,
    apply_size_modifier,
    apply_spray,
    compute_damage,
    lands,
)

RIFLE = WeaponType(class_name="Assault", category="Medium Arms")


class SequenceRng(random.Random):
    """Hands out the given rolls in order, and fails when the code asks for one more than it was given."""

    def __init__(self, values):
        super().__init__()
        self._values = list(values)
        self._index = 0

    def randint(self, a, b):
        value = self._values[self._index]
        self._index += 1
        return value


def loaded(name):
    gun = Catalog.create(name)
    gun.reload()
    return gun


class CombatMathTests(unittest.TestCase):
    def test_close_range_bonus_uses_50m_bands(self):
        self.assertEqual(apply_range_modifier(51, 100, RIFLE, 50), 50)
        self.assertEqual(apply_range_modifier(50, 100, RIFLE, 50), 45)
        self.assertEqual(apply_range_modifier(49, 100, RIFLE, 50), 45)

    def test_far_range_penalty(self):
        self.assertEqual(apply_range_modifier(150, 100, RIFLE, 50), 60)
        self.assertEqual(apply_range_modifier(100, 100, RIFLE, 50), 50)

    def test_close_bonus_is_capped(self):
        self.assertEqual(apply_range_modifier(0, 500, RIFLE, 80), 65)

    def test_sniper_is_penalised_up_close(self):
        self.assertEqual(apply_range_modifier(400, 500, SNIPER, 80), 90)
        self.assertEqual(apply_range_modifier(0, 500, SNIPER, 80), 100)

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
        self.assertAlmostEqual(apply_spray(10, 150), 100)

    def test_spray_control_scales_the_widening_only(self):
        self.assertAlmostEqual(apply_spray(10, 8, control=0.8), 18)
        self.assertAlmostEqual(apply_spray(10, 2, control=1.4), 12.8)
        self.assertEqual(apply_spray(10, 1, control=1.4), 10)

    def test_cover_and_movement_add_to_the_roll(self):
        self.assertEqual(apply_cover_modifier(Target(100), 50), 50)
        self.assertEqual(apply_cover_modifier(Target(100, cover="light"), 50), 60)
        self.assertEqual(apply_cover_modifier(Target(100, cover="heavy"), 50), 75)
        self.assertEqual(apply_cover_modifier(Target(100, moving=True), 50), 60)
        self.assertEqual(apply_cover_modifier(Target(100, cover="heavy", moving=True), 50), 85)

    def test_unknown_size_or_cover_is_rejected(self):
        with self.assertRaises(ValueError):
            Target(100, "x")
        with self.assertRaises(ValueError):
            Target(100, cover="bunker")

    def test_damage_falls_in_a_line_to_the_floor_at_max_range(self):
        self.assertEqual(compute_damage(100, 100, 200, 50), 50)
        self.assertEqual(compute_damage(149, 100, 200, 50), 50)
        self.assertEqual(compute_damage(150, 100, 200, 50), 38)
        self.assertEqual(compute_damage(200, 100, 200, 50), 25)
        self.assertEqual(compute_damage(500, 100, 200, 50), 25)
        self.assertEqual(compute_damage(300, 200, 450, 75), 55)

    def test_flat_damage_when_base_and_max_range_meet(self):
        self.assertEqual(compute_damage(500, 500, 500, 100), 100)

    def test_damage_under_the_floor_does_not_grow(self):
        self.assertEqual(compute_damage(200, 100, 200, 10), 10)

    def test_every_weapon_still_hurts_at_its_max_range(self):
        for weapon in Catalog.all():
            with self.subTest(weapon=weapon.name):
                at_max = compute_damage(weapon.max_range, weapon.range_m, weapon.max_range, weapon.damage)
                self.assertGreaterEqual(at_max, MIN_DAMAGE)
                self.assertGreaterEqual(hit_chance(weapon, Target(weapon.max_range)), 0.02)


class ToHitTests(unittest.TestCase):
    def test_natural_rolls_ignore_the_modifiers(self):
        gun, far = Catalog.create("M1911"), Target(200)
        self.assertTrue(lands(2, gun, far))
        self.assertFalse(lands(99, gun, far))
        self.assertTrue(lands(60, gun, far))
        self.assertFalse(lands(61, gun, far))

    def test_size_scales_the_roll_but_not_the_range_penalty(self):
        gun, large_far = Catalog.create("M1911"), Target(200, "l")
        self.assertTrue(lands(66, gun, large_far))
        self.assertFalse(lands(67, gun, large_far))

    def test_hit_chance_matches_the_rolls(self):
        gun = Catalog.create("M1911")
        self.assertAlmostEqual(hit_chance(gun, Target(100)), 0.80)
        self.assertAlmostEqual(hit_chance(gun, Target(50)), 0.85)
        self.assertEqual(hit_chance(gun, Target(201)), 0.0)

    def test_a_shotgun_lands_when_any_pellet_does(self):
        shotgun = Catalog.create("W1200")
        self.assertAlmostEqual(hit_chance(shotgun, Target(100)), 1 - 0.1 ** shotgun.pellets)

    def test_spray_control_separates_the_classes_in_a_long_string(self):
        lmg, pistol = Catalog.create("M249 SAW"), Catalog.create("Glock 18")
        self.assertTrue(lands(44, lmg, Target(300), shots_in_string=9))
        self.assertFalse(lands(32, pistol, Target(150), shots_in_string=9))
        self.assertTrue(lands(32, lmg, Target(300), shots_in_string=9))


class ResolveShotTests(unittest.TestCase):
    def test_sniper_deals_damage_at_max_range(self):
        result = resolve_shot(loaded("M40A3"), Target(500, "m"), rng=SequenceRng([30, 100, 1000]))
        self.assertTrue(result.hit)
        self.assertEqual((result.damage, result.critical, result.pellets_hit), (100, False, 1))

    def test_beyond_max_range_is_a_miss(self):
        result = resolve_shot(loaded("M40A3"), Target(501, "m"), rng=SequenceRng([]))
        self.assertFalse(result.hit)
        self.assertEqual(result.damage, 0)
        self.assertEqual(result.remaining_ammo, 4)

    def test_damage_varies_per_hit(self):
        low = resolve_shot(loaded("M16A4"), Target(200), rng=SequenceRng([30, 85, 1000]))
        high = resolve_shot(loaded("M16A4"), Target(200), rng=SequenceRng([30, 115, 1000]))
        self.assertEqual((low.damage, high.damage), (64, 86))

    def test_a_hit_at_max_range_does_the_floor_damage(self):
        result = resolve_shot(loaded("M16A4"), Target(450, "m"), rng=SequenceRng([1, 100, 1000]))
        self.assertTrue(result.hit)
        self.assertEqual(result.damage, MIN_DAMAGE)

    def test_critical_hits_double_or_triple(self):
        triple = resolve_shot(loaded("M1911"), Target(100), rng=SequenceRng([30, 100, 1, 50]))
        double = resolve_shot(loaded("M1911"), Target(100), rng=SequenceRng([30, 100, 30, 10]))
        plain = resolve_shot(loaded("M1911"), Target(100), rng=SequenceRng([30, 100, 31]))
        self.assertEqual([r.damage for r in (triple, double, plain)], [150, 100, 50])
        self.assertEqual([r.critical for r in (triple, double, plain)], [True, True, False])

    def test_a_long_string_misses_what_a_single_shot_hits(self):
        single = resolve_shot(loaded("G36"), Target(50, "m"), shots_in_string=1, rng=SequenceRng([30, 100, 1000]))
        sprayed = resolve_shot(loaded("G36"), Target(50, "m"), shots_in_string=31, rng=SequenceRng([30]))
        self.assertTrue(single.hit)
        self.assertFalse(sprayed.hit)

    def test_cover_turns_a_hit_into_a_miss(self):
        open_target = resolve_shot(loaded("M1911"), Target(100), rng=SequenceRng([75, 100, 1000]))
        covered = resolve_shot(loaded("M1911"), Target(100, cover="heavy"), rng=SequenceRng([75]))
        self.assertTrue(open_target.hit)
        self.assertFalse(covered.hit)

    def test_shotgun_damage_is_the_share_of_pellets_that_land(self):
        shotgun = loaded("W1200")
        rolls = [10] * 5 + [99] * 3 + [100, 1000]
        result = resolve_shot(shotgun, Target(100), rng=SequenceRng(rolls))
        self.assertEqual((result.hit, result.pellets_hit, result.damage), (True, 5, 47))
        whiff = resolve_shot(shotgun, Target(100), rng=SequenceRng([99] * 8))
        self.assertEqual((whiff.hit, whiff.pellets_hit, whiff.damage), (False, 0, 0))

    def test_empty_weapon_cannot_fire(self):
        gun = Catalog.create("Barrett .50Cal")
        first = resolve_shot(gun, Target(50, "m"), rng=SequenceRng([]))
        self.assertFalse(first.hit)
        self.assertFalse(first.fired)
        self.assertEqual(first.remaining_ammo, 0)

        gun.current_ammo = 1
        live = resolve_shot(gun, Target(50, "m"), rng=SequenceRng([1, 100, 1000]))
        empty = resolve_shot(gun, Target(50, "m"), rng=SequenceRng([]))
        self.assertTrue(live.hit)
        self.assertFalse(empty.hit)
        self.assertEqual(empty.remaining_ammo, 0)
        self.assertEqual(gun.current_ammo, 0)


if __name__ == "__main__":
    unittest.main()
