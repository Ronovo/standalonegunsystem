import unittest

from gunsystem import Catalog


class CatalogTests(unittest.TestCase):
    def test_create_returns_independent_ammo_state(self):
        first = Catalog.create("M1911")
        second = Catalog.create("M1911")
        first.reload()
        first.fire_shot()
        self.assertEqual(first.current_ammo, 6)
        self.assertEqual(second.current_ammo, 0)

    def test_catalog_includes_all_weapons(self):
        names = Catalog.names()
        self.assertEqual(len(names), 26)
        self.assertIn("Spas-12", names)
        self.assertEqual(len(Catalog.all()), 26)

    def test_unknown_weapon_raises(self):
        with self.assertRaises(KeyError):
            Catalog.create("Not A Gun")

    def test_copy_does_not_share_ammo(self):
        gun = Catalog.create("MP5")
        gun.reload()
        clone = gun.copy()
        gun.fire_shot()
        self.assertEqual(gun.current_ammo, 29)
        self.assertEqual(clone.current_ammo, 30)


if __name__ == "__main__":
    unittest.main()
