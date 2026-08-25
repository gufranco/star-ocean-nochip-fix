from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from starocean import editions, errors, fix


def reaching_back(source: str) -> list[str]:
    """Every import in that source that comes from this package rather than outside it.

    Written against text rather than against the one file it guards, so it can be
    handed something that should fail it. A reader nobody has seen report a fault
    reports a clean run whether or not there is one.

    A relative import counts however deep it goes, and an absolute one counts
    when it is the package or a module under it. The dot is required, because a
    package whose name merely begins the same way is somebody else's.
    """

    def inside(name: str) -> bool:
        return name.startswith(".") or name == "starocean" or name.startswith("starocean.")

    borrowed = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            borrowed += [alias.name for alias in node.names if inside(alias.name)]
        elif isinstance(node, ast.ImportFrom):
            name = "." * node.level + (node.module or "")
            if inside(name):
                borrowed.append(name)
    return borrowed


class OneHomeTest(unittest.TestCase):
    """That every refusal this package makes is defined here and nowhere else.

    Two classes under one name both work, both get tested, and `except` catches
    half the cases it names. Keeping them in one module is what makes that
    impossible rather than unlikely, and it matters more here than elsewhere:
    every one of these refusals is a reason a reader's file was not the one the
    manifest names, and a caller distinguishing between them is the whole point.
    """

    def named(self) -> list[str]:
        return [
            name
            for name, held in vars(errors).items()
            if isinstance(held, type) and issubclass(held, Exception)
        ]

    def test_the_module_defines_every_refusal_this_package_makes(self) -> None:
        self.assertEqual(
            sorted(self.named()),
            ["Corrupt", "Missing", "NotACartridge", "Unexpected", "UnknownEdition", "Unrecognised"],
        )

    def test_every_one_of_them_derives_from_exception(self) -> None:
        stray = [name for name in self.named() if not issubclass(getattr(errors, name), Exception)]

        self.assertEqual(stray, [])

    def test_and_every_one_says_what_it_means(self) -> None:
        """A refusal a caller meets and cannot look up is a refusal they guess at."""
        silent = [
            name for name in self.named() if not (getattr(errors, name).__doc__ or "").strip()
        ]

        self.assertEqual(silent, [])

    def test_none_of_them_is_a_subclass_of_another(self) -> None:
        """Or catching one would silently catch the other.

        These six exist to be told apart. A reader whose file was refused wants
        to know which refusal it was, because the fix differs: a stub to strip, a
        set to join, a different revision to find, or a corrupt download.
        """
        held = [getattr(errors, name) for name in self.named()]

        overlapping = [
            (one.__name__, other.__name__)
            for one in held
            for other in held
            if one is not other and issubclass(one, other)
        ]

        self.assertEqual(overlapping, [])


class OneClassPerNameTest(unittest.TestCase):
    """That every module reaching for a refusal reaches for the same object.

    Identity rather than name. Two classes under one name compare equal by name
    and are different objects, which is what makes the duplicate survive testing.
    """

    def test_the_fix_raises_the_ones_defined_here(self) -> None:
        held = {
            getattr(fix, name)
            for name in ("NotACartridge", "Unrecognised", "Corrupt", "Unexpected", "Missing")
        }

        self.assertEqual(
            held,
            {
                errors.NotACartridge,
                errors.Unrecognised,
                errors.Corrupt,
                errors.Unexpected,
                errors.Missing,
            },
        )

    def test_and_the_catalogue_raises_the_one_unknown_edition(self) -> None:
        self.assertIs(getattr(editions, "UnknownEdition"), errors.UnknownEdition)  # noqa: B009

    def test_naming_an_edition_this_package_does_not_cover_raises_it(self) -> None:
        with self.assertRaises(errors.UnknownEdition):
            editions.named("some other game")

    def test_and_the_refusal_names_the_editions_it_does_cover(self) -> None:
        """A refusal that does not say what would have worked costs a search."""
        with self.assertRaises(errors.UnknownEdition) as caught:
            editions.named("some other game")

        self.assertIn("japanese", str(caught.exception))


class NoCycleTest(unittest.TestCase):
    """That this module imports nothing from the package it belongs to.

    Everything here raises, so everything here imports this. An import running
    the other way closes the cycle and makes the order modules happen to load in
    decide whether the package works.
    """

    def test_it_imports_nothing_from_this_package(self) -> None:
        held = (ROOT / "starocean" / "errors.py").read_text()

        self.assertEqual(reaching_back(held), [])

    def test_the_reader_of_that_names_an_absolute_import_back(self) -> None:
        found = reaching_back("import starocean.fix\n")

        self.assertEqual(found, ["starocean.fix"])

    def test_and_a_relative_one(self) -> None:
        found = reaching_back("from . import fix\n")

        self.assertEqual(found, ["."])

    def test_and_steps_over_one_from_outside(self) -> None:
        """The standard library, the member this one consumes, and a lookalike name."""
        found = reaching_back(
            "from __future__ import annotations\nimport romimage\nimport staroceantools\n"
        )

        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
