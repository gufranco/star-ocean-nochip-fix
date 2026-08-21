"""Hold this package's two constants to hardware.json, and to their standing.

Almost nothing is pinned here, because almost nothing belongs here: what a header
means is pinned in snes-rom-image-python against Nintendo's manual, and copying
it would make a second source of truth that drifts. What is left is the image
length and the size byte that follows from it, and this holds both to the record
and to every edition in the manifest.
"""

import json
import sys
import unittest
from pathlib import Path
from typing import Any, override

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "snes-rom-image-python"))
sys.path.insert(0, str(ROOT / "snes-rom-image-python" / "snes-mapper-python"))

from romimage import rewrite

from starocean import editions

HERE = Path(__file__).resolve().parent

KILOBYTE = 1024


def declared(name: str) -> dict[str, Any]:
    held = json.loads((HERE / name).read_text())
    assert isinstance(held, dict), f"{name} does not hold an object"
    return held


class DocumentTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.declared = declared("hardware.json")

    def test_the_authority_points_at_the_siblings_rather_than_repeating_them(self) -> None:
        order = self.declared["authority"]["order"]

        self.assertIn("snes-rom-image-python", order[0])

    def test_and_says_why_nothing_is_copied_here(self) -> None:
        note = self.declared["note"]

        self.assertIn("second source of truth", note)

    def test_what_this_package_does_not_claim_is_recorded(self) -> None:
        stated = self.declared["notStated"]

        self.assertGreaterEqual(len(stated), 4)

    def test_every_fact_names_its_evidence(self) -> None:
        missing = [
            name for name, fact in self.declared["facts"].items() if not fact.get("evidence")
        ]

        self.assertEqual(missing, [])


class ConstantTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.facts: dict[str, Any] = declared("hardware.json")["facts"]

    def test_the_declared_length_is_the_one_this_package_expects(self) -> None:
        length = self.facts["imageBytes"]

        self.assertEqual(length["value"], editions.EXPECTED_BYTES)

    def test_and_it_is_ninety_six_megabit(self) -> None:
        length = self.facts["imageBytes"]["value"]

        self.assertEqual(length * 8 // KILOBYTE // KILOBYTE, 96)

    def test_every_edition_in_the_manifest_is_that_length(self) -> None:
        wrong = [
            edition.name for edition in editions.EDITIONS if edition.size != editions.EXPECTED_BYTES
        ]

        self.assertEqual(wrong, [])

    def test_the_declared_size_byte_follows_from_nintendos_rule(self) -> None:
        declared_byte = self.facts["sizeByte"]["value"]

        self.assertEqual(declared_byte, rewrite.size_byte(editions.EXPECTED_BYTES))

    def test_and_the_record_says_it_comes_from_a_rule_rather_than_a_row(self) -> None:
        note = self.facts["sizeByte"]["note"]

        self.assertIn("table stops at 32 megabit", note)


class ManifestTest(unittest.TestCase):
    """The digests, which are what makes this safe to run without watching it."""

    def test_every_edition_names_a_file_before_and_after(self) -> None:
        missing = [
            edition.name for edition in editions.EDITIONS if not (edition.reads and edition.writes)
        ]

        self.assertEqual(missing, [])

    def test_every_edition_carries_four_digests_at_each_end(self) -> None:
        wrong = [
            edition.name
            for edition in editions.EDITIONS
            if sorted(edition.before) != sorted(editions.DIGESTS)
            or sorted(edition.after) != sorted(editions.DIGESTS)
        ]

        self.assertEqual(wrong, [])

    def test_only_one_of_the_four_decides(self) -> None:
        self.assertEqual(editions.DECIDES, "sha256")

    def test_and_it_is_the_widest_of_them(self) -> None:
        widest = max(editions.DIGEST_WIDTHS, key=lambda name: editions.DIGEST_WIDTHS[name])

        self.assertEqual(widest, editions.DECIDES)

    def test_no_two_editions_read_the_same_file(self) -> None:
        reads = [edition.reads for edition in editions.EDITIONS]

        self.assertEqual(len(set(reads)), len(reads))

    def test_and_no_two_produce_the_same_result(self) -> None:
        after = [edition.after[editions.DECIDES] for edition in editions.EDITIONS]

        self.assertEqual(len(set(after)), len(after))


class DivergenceTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.entries: list[dict[str, Any]] = declared("divergences.json")["divergences"]

    def test_each_entry_says_which_source_the_package_follows(self) -> None:
        allowed = {"document", "reference", "neither"}

        self.assertEqual({entry["packageFollows"] for entry in self.entries} - allowed, set())

    def test_each_entry_says_what_would_settle_it(self) -> None:
        missing = [entry["id"] for entry in self.entries if not entry.get("wouldSettleIt")]

        self.assertEqual(missing, [])

    def test_the_input_being_a_hack_is_recorded_as_a_boundary(self) -> None:
        entry = next(
            item
            for item in self.entries
            if item["id"] == "the-input-is-a-hack-and-that-is-the-point"
        )

        self.assertIn("it is the subject", entry["reasoning"])

    def test_and_that_this_package_models_no_hardware(self) -> None:
        named = {entry["id"] for entry in self.entries}

        self.assertIn("nothing-here-models-hardware", named)


if __name__ == "__main__":
    unittest.main(verbosity=1)
