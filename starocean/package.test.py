import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import starocean


class ExportTest(unittest.TestCase):
    def test_the_package_offers_a_deliberate_surface(self):
        self.assertTrue(starocean.__all__)

    def test_every_name_it_offers_is_there(self):
        for name in starocean.__all__:
            self.assertTrue(hasattr(starocean, name), name)

    def test_the_names_are_grouped_constants_then_classes_then_functions(self):
        def rank(name):
            if name.isupper():
                return 0
            return 1 if name[0].isupper() else 2

        ranks = [rank(name) for name in starocean.__all__]

        self.assertEqual(ranks, sorted(ranks))

    def test_each_group_is_in_order_within_itself(self):
        def rank(name):
            if name.isupper():
                return 0
            return 1 if name[0].isupper() else 2

        for group in (0, 1, 2):
            held = [name for name in starocean.__all__ if rank(name) == group]

            self.assertEqual(held, sorted(held), group)

    def test_no_name_is_offered_twice(self):
        self.assertEqual(len(starocean.__all__), len(set(starocean.__all__)))

    def test_the_version_is_the_one_the_release_script_writes(self):
        self.assertEqual(starocean.__version__, starocean.VERSION)

    def test_both_entry_points_are_reachable_from_the_package(self):
        for name in ("look", "report", "verdict", "apply", "run", "correct"):
            self.assertIn(name, starocean.__all__)

    def test_nothing_private_leaks_into_the_surface(self):
        for name in starocean.__all__:
            self.assertFalse(name.startswith("_"), name)


class ConsoleTest(unittest.TestCase):
    def setUp(self):
        with (ROOT / "pyproject.toml").open("rb") as handle:
            self.held = tomllib.load(handle)

    def test_the_package_declares_the_commands_it_installs(self):
        self.assertTrue(self.held["project"]["scripts"])

    def test_every_command_points_at_something_importable(self):
        for command, target in self.held["project"]["scripts"].items():
            module, _, attribute = target.partition(":")
            imported = __import__(module, fromlist=[attribute])

            self.assertTrue(callable(getattr(imported, attribute)), command)

    def test_a_command_exists_for_correcting_and_one_for_checking(self):
        named = set(self.held["project"]["scripts"])

        self.assertEqual(named, {"star-ocean-fix", "star-ocean-verify"})

    def test_the_packaged_name_matches_the_directory_it_ships(self):
        self.assertIn(starocean.__name__, self.held["tool"]["setuptools"]["packages"])


if __name__ == "__main__":
    unittest.main()
