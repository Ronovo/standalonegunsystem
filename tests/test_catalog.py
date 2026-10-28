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
        names = [weapon.name for weapon in Catalog.all()]
        self.assertEqual(len(names), 26)
        self.assertIn("Spas-12", names)

    def test_unknown_weapon_raises(self):
        with self.assertRaises(KeyError):
            Catalog.create("Not A Gun")


if __name__ == "__main__":
    unittest.main()
