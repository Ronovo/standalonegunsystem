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

    def test_rounds_per_pull_follow_the_rate_of_fire(self):
        pulls = {name: Catalog.create(name).rounds_per_pull for name in ("MP5", "USAS-12", "Glock 18", "W1200")}
        self.assertEqual(pulls, {"MP5": 13, "USAS-12": 5, "Glock 18": 20, "W1200": 1})

    def test_reload_labels_name_the_style(self):
        self.assertEqual(Catalog.create("M1911").reload_label, "2 s")
        self.assertEqual(Catalog.create("M1911").full_reload_seconds, 2.0)
        self.assertEqual(Catalog.create("W1200").full_reload_seconds, 4.2)
        self.assertEqual(Catalog.create("W1200").reload_label, "0.6 s per shell (4.2 s from empty)")
        self.assertEqual(Catalog.create(".38 Special").reload_label, "0.8 s per round (4.8 s from empty)")

    def test_describe_lists_the_new_stats(self):
        text = Catalog.create("Spas-12").describe()
        self.assertIn("Rate of Fire: 100 rpm | Reload: 0.6 s per shell (4.8 s from empty)", text)
        self.assertIn("Pellets Per Shell: 8", text)
        self.assertNotIn("Pellets", Catalog.create("M1911").describe())


if __name__ == "__main__":
    unittest.main()
