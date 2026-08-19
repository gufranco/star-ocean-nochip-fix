"""The checks that need the real images, which is why they live apart.

A skipped test contributes no coverage, so on a runner with an empty directory
every line here would read as uncovered and fail the coverage gate for a reason
that has nothing to do with the code. Keeping them in one file lets that file sit
outside the gate while everything else stays inside it.

What they prove is the thing the unit tests cannot: that the digests written down
in the manifest are the digests these two files actually have, and that correcting
them really does produce what was promised. Everything else is a stand-in.
"""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from starocean import editions, fix

sys.path.insert(0, str(ROOT / "packages" / "snes-rom-image"))
sys.path.insert(0, str(ROOT / "packages" / "snes-rom-image" / "packages" / "snes-mapper"))

import mapper
from romimage import rewrite

SOURCE = fix.source_directory()

PRESENT = tuple(edition for edition in editions.EDITIONS if (SOURCE / edition.reads).is_file())

WHY_NOT = (
    "neither image was found: these read a rebuild somebody else made, and it is"
    " theirs, so a copy you already own goes in the roms directory of this"
    f" repository or wherever {fix.DIRECTORY_VARIABLE} points"
)


@unittest.skipUnless(PRESENT, WHY_NOT)
class SourceTest(unittest.TestCase):
    def test_every_image_present_is_the_length_the_manifest_pins(self):
        for edition in PRESENT:
            self.assertEqual((SOURCE / edition.reads).stat().st_size, edition.size, edition.name)

    def test_every_image_present_matches_all_four_of_its_pinned_digests(self):
        for edition in PRESENT:
            found = fix.digests_of((SOURCE / edition.reads).read_bytes())

            for digest in editions.DIGESTS:
                self.assertEqual(found[digest], edition.before[digest], (edition.name, digest))

    def test_every_image_present_still_claims_the_chip_it_no_longer_has(self):
        for edition in PRESENT:
            image = (SOURCE / edition.reads).read_bytes()

            self.assertTrue(rewrite.needs_rewrite(image), edition.name)


@unittest.skipUnless(PRESENT, WHY_NOT)
class ResultTest(unittest.TestCase):
    def test_correcting_each_one_produces_exactly_what_was_promised(self):
        for edition in PRESENT:
            produced = fix.apply((SOURCE / edition.reads).read_bytes(), edition)
            found = fix.digests_of(produced)

            for digest in editions.DIGESTS:
                self.assertEqual(found[digest], edition.after[digest], (edition.name, digest))

    def test_the_result_declares_no_coprocessor_and_the_length_it_has(self):
        for edition in PRESENT:
            produced = fix.apply((SOURCE / edition.reads).read_bytes(), edition)

            self.assertFalse(rewrite.needs_rewrite(produced), edition.name)

    def test_the_result_carries_a_checksum_that_covers_it(self):
        for edition in PRESENT:
            produced = fix.apply((SOURCE / edition.reads).read_bytes(), edition)
            places = rewrite.mirrors(produced)
            declared = mapper.read(produced)

            self.assertEqual(rewrite.checksum(produced, places), declared.checksum, edition.name)
            self.assertTrue(declared.checksum_agrees, edition.name)

    def test_the_result_is_still_a_twelve_megabyte_low_declaration(self):
        for edition in PRESENT:
            produced = fix.apply((SOURCE / edition.reads).read_bytes(), edition)
            declared = mapper.read(produced)

            self.assertEqual(len(produced), editions.EXPECTED_BYTES, edition.name)
            self.assertEqual(declared.layout, mapper.header.LOROM, edition.name)
            self.assertEqual(declared.at, 0x7FC0, edition.name)

    def test_only_the_header_mirrors_are_touched(self):
        for edition in PRESENT:
            image = (SOURCE / edition.reads).read_bytes()
            produced = fix.apply(image, edition)
            places = set(rewrite.mirrors(image))

            moved = [at for at in range(len(image)) if image[at] != produced[at]]

            self.assertTrue(moved, edition.name)
            for at in moved:
                self.assertTrue(
                    any(place <= at < place + 32 for place in places),
                    (edition.name, hex(at)),
                )

    def test_correcting_a_corrected_image_changes_nothing_further(self):
        for edition in PRESENT:
            produced = fix.apply((SOURCE / edition.reads).read_bytes(), edition)

            self.assertEqual(fix.correct(produced), produced, edition.name)


@unittest.skipUnless(PRESENT, WHY_NOT)
class RunTest(unittest.TestCase):
    def test_each_one_is_written_out_under_the_name_it_was_given(self):
        into = Path(tempfile.mkdtemp())

        for edition in PRESENT:
            written = fix.run(edition, SOURCE, into)

            self.assertEqual(written.name, edition.writes)
            self.assertEqual(fix.digests_of(written.read_bytes()), edition.after)


if __name__ == "__main__":
    unittest.main()
