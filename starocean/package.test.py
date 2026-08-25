import sys
import tomllib
import unittest
from pathlib import Path
from typing import override

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import starocean


class ExportTest(unittest.TestCase):
    def test_the_package_offers_a_deliberate_surface(self) -> None:
        self.assertTrue(starocean.__all__)

    def test_every_name_it_offers_is_there(self) -> None:
        for name in starocean.__all__:
            self.assertTrue(hasattr(starocean, name), name)

    def test_the_names_are_grouped_constants_then_classes_then_functions(self) -> None:
        def rank(name: str) -> int:
            if name.isupper():
                return 0
            return 1 if name[0].isupper() else 2

        ranks = [rank(name) for name in starocean.__all__]

        self.assertEqual(ranks, sorted(ranks))

    def test_each_group_is_in_order_within_itself(self) -> None:
        def rank(name: str) -> int:
            if name.isupper():
                return 0
            return 1 if name[0].isupper() else 2

        for group in (0, 1, 2):
            held = [name for name in starocean.__all__ if rank(name) == group]

            self.assertEqual(held, sorted(held), group)

    def test_no_name_is_offered_twice(self) -> None:
        self.assertEqual(len(starocean.__all__), len(set(starocean.__all__)))

    def test_the_version_is_the_one_the_release_script_writes(self) -> None:
        self.assertEqual(starocean.__version__, starocean.VERSION)

    def test_both_entry_points_are_reachable_from_the_package(self) -> None:
        for name in ("look", "report", "verdict", "apply", "run", "correct"):
            self.assertIn(name, starocean.__all__)

    def test_nothing_private_leaks_into_the_surface(self) -> None:
        for name in starocean.__all__:
            self.assertFalse(name.startswith("_"), name)


class PackagingTest(unittest.TestCase):
    """That this repository ships no packaging block, which is deliberate.

    It consumes `snes-rom-image` as a submodule rather than as a version range.
    A wheel built from here installs cleanly and then raises on its first import,
    because the submodule is not in it and cannot be, so a `[project]` block
    would let somebody `pip install git+...` and receive exactly that. The readme
    says the same thing in prose, and the two commands are run as files.
    """

    @override
    def setUp(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as handle:
            self.held = tomllib.load(handle)

    def test_the_manifest_declares_no_package(self) -> None:
        self.assertNotIn("project", self.held)

    def test_nor_a_way_to_build_one(self) -> None:
        self.assertNotIn("build-system", self.held)

    def test_it_still_configures_every_checker(self) -> None:
        self.assertTrue(self.held["tool"]["ruff"])
        self.assertTrue(self.held["tool"]["mypy"])
        self.assertTrue(self.held["tool"]["coverage"])

    def test_the_readme_says_what_is_run_instead(self) -> None:
        held = (ROOT / "README.md").read_text()

        self.assertIn("python3 starocean/verify.py", held)
        self.assertIn("python3 starocean/fix.py", held)

    def test_and_says_why_there_is_nothing_to_install(self) -> None:
        held = (ROOT / "README.md").read_text()

        self.assertIn("ships\nno packaging block", held)


if __name__ == "__main__":
    unittest.main()
