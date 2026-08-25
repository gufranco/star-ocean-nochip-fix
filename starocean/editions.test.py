import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starocean import editions
from starocean.errors import UnknownEdition


class CatalogueTest(unittest.TestCase):
    def test_both_editions_are_listed(self) -> None:
        self.assertEqual(len(editions.EDITIONS), 2)

    def test_each_edition_has_a_name_of_its_own(self) -> None:
        names = [edition.name for edition in editions.EDITIONS]

        self.assertEqual(len(names), len(set(names)))

    def test_each_edition_names_the_file_it_reads_and_the_file_it_writes(self) -> None:
        for edition in editions.EDITIONS:
            self.assertTrue(edition.reads)
            self.assertTrue(edition.writes)
            self.assertNotEqual(edition.reads, edition.writes)

    def test_both_editions_are_the_same_length(self) -> None:
        lengths = {edition.size for edition in editions.EDITIONS}

        self.assertEqual(lengths, {editions.EXPECTED_BYTES})

    def test_that_length_is_the_one_the_whole_bank_map_has(self) -> None:
        self.assertEqual(editions.EXPECTED_BYTES, 0xC00000)

    def test_an_edition_prints_as_its_name_and_length(self) -> None:
        printed = repr(editions.EDITIONS[0])

        self.assertIn(editions.EDITIONS[0].name, printed)
        self.assertIn(str(editions.EDITIONS[0].size), printed)

    def test_the_table_is_read_from_the_manifest_rather_than_written_in_code(self) -> None:
        self.assertTrue(editions.MANIFEST.is_file())
        self.assertEqual(len(editions.load()), len(editions.EDITIONS))

    def test_a_manifest_somewhere_else_can_be_read_instead(self) -> None:
        import json
        import tempfile

        where = Path(tempfile.mkdtemp()) / "other.json"
        where.write_text(json.dumps({"editions": []}))

        self.assertEqual(editions.load(where), ())


class DigestTest(unittest.TestCase):
    def test_every_edition_pins_all_four_digests_of_what_it_reads(self) -> None:
        for edition in editions.EDITIONS:
            for name, width in editions.DIGEST_WIDTHS.items():
                self.assertEqual(len(edition.before[name]), width, (edition.name, name))

    def test_and_all_four_of_what_it_writes(self) -> None:
        for edition in editions.EDITIONS:
            for name, width in editions.DIGEST_WIDTHS.items():
                self.assertEqual(len(edition.after[name]), width, (edition.name, name))

    def test_no_edition_reads_and_writes_the_same_bytes(self) -> None:
        for edition in editions.EDITIONS:
            self.assertNotEqual(edition.before[editions.DECIDES], edition.after[editions.DECIDES])

    def test_no_two_editions_share_a_deciding_digest(self) -> None:
        seen = [edition.before[editions.DECIDES] for edition in editions.EDITIONS]
        seen += [edition.after[editions.DECIDES] for edition in editions.EDITIONS]

        self.assertEqual(len(seen), len(set(seen)))

    def test_every_digest_is_written_in_lower_case_hexadecimal(self) -> None:
        for edition in editions.EDITIONS:
            for held in (edition.before, edition.after):
                for value in held.values():
                    self.assertRegex(value, r"^[0-9a-f]+$")


class ChainTest(unittest.TestCase):
    """Every file between a cartridge somebody owns and the corrected image.

    Pinning only the patched image tells a reader what to end up with and nothing
    about how to get there. The chain is the retail cartridge, the patch applied
    to it, the image that produces, and the image this writes.
    """

    def test_the_patch_is_named_with_its_author_and_where_it_lives(self) -> None:
        self.assertEqual(editions.PATCH.author, "neviksti")
        self.assertTrue(editions.PATCH.where.startswith("https://"))
        self.assertTrue(editions.PATCH.version)

    def test_the_archive_carrying_the_patch_is_pinned(self) -> None:
        for digest, width in editions.DIGEST_WIDTHS.items():
            self.assertEqual(len(str(editions.PATCH.archive[digest])), width, digest)

    def test_every_edition_names_the_cartridge_it_starts_from(self) -> None:
        for edition in editions.EDITIONS:
            self.assertTrue(edition.source["name"])
            self.assertGreater(edition.source["bytes"], 0)

    def test_and_the_patch_that_turns_it_into_the_image_read(self) -> None:
        for edition in editions.EDITIONS:
            self.assertTrue(edition.patch["name"].endswith(".xdelta"))

    def test_each_edition_uses_a_patch_of_its_own(self) -> None:
        used = [edition.patch["name"] for edition in editions.EDITIONS]

        self.assertEqual(len(used), len(set(used)))

    def test_each_edition_starts_from_a_cartridge_of_its_own(self) -> None:
        used = [edition.source["sha256"] for edition in editions.EDITIONS]

        self.assertEqual(len(used), len(set(used)))

    def test_every_link_in_the_chain_pins_all_four_digests(self) -> None:
        for edition in editions.EDITIONS:
            for link in (edition.source, edition.patch, edition.before, edition.after):
                for digest, width in editions.DIGEST_WIDTHS.items():
                    self.assertEqual(len(link[digest]), width, (edition.name, digest))

    def test_the_cartridge_is_smaller_than_what_the_patch_makes_of_it(self) -> None:
        for edition in editions.EDITIONS:
            self.assertLess(edition.source["bytes"], edition.size, edition.name)

    def test_every_link_of_every_edition_is_a_distinct_file(self) -> None:
        seen = [
            link["sha256"]
            for edition in editions.EDITIONS
            for link in (edition.source, edition.patch, edition.before, edition.after)
        ]

        self.assertEqual(len(seen), len(set(seen)))

    def test_the_chain_is_offered_in_the_order_it_is_walked(self) -> None:
        walked = editions.EDITIONS[0].chain()

        self.assertEqual(
            [step.what for step in walked],
            ["source", "patch", "reads", "writes"],
        )

    def test_every_step_of_the_chain_carries_a_name_and_a_length(self) -> None:
        for edition in editions.EDITIONS:
            for step in edition.chain():
                self.assertTrue(step.name, (edition.name, step.what))
                self.assertGreater(step.bytes, 0, (edition.name, step.what))

    def test_a_step_prints_as_what_it_is_and_what_it_names(self) -> None:
        step = editions.EDITIONS[0].chain()[0]

        self.assertIn(step.what, repr(step))
        self.assertIn(step.name, repr(step))

    def test_a_patch_prints_as_its_name_version_and_author(self) -> None:
        printed = repr(editions.PATCH)

        self.assertIn(editions.PATCH.author, printed)
        self.assertIn(editions.PATCH.version, printed)

    def test_a_step_offers_the_digest_that_decides_and_any_other(self) -> None:
        step = editions.EDITIONS[0].chain()[0]

        self.assertEqual(step.digest(), step.held[editions.DECIDES])
        self.assertEqual(step.digest("crc32"), step.held["crc32"])

    def test_only_the_last_step_is_one_this_repository_produces(self) -> None:
        for edition in editions.EDITIONS:
            produced = [step.what for step in edition.chain() if step.produced]

            self.assertEqual(produced, ["writes"])


class LookupTest(unittest.TestCase):
    def test_an_edition_is_found_by_the_digest_of_what_it_reads(self) -> None:
        wanted = editions.EDITIONS[0]

        self.assertIs(editions.matching(wanted.before[editions.DECIDES]), wanted)

    def test_a_digest_no_edition_carries_finds_nothing(self) -> None:
        self.assertIsNone(editions.matching("0" * 64))

    def test_an_edition_is_found_by_name(self) -> None:
        wanted = editions.EDITIONS[0]

        self.assertIs(editions.named(wanted.name), wanted)

    def test_a_name_no_edition_carries_is_refused(self) -> None:
        with self.assertRaises(UnknownEdition):
            editions.named("nonsense")

    def test_the_refusal_lists_the_editions_there_are(self) -> None:
        with self.assertRaises(UnknownEdition) as raised:
            editions.named("nonsense")

        for edition in editions.EDITIONS:
            self.assertIn(edition.name, str(raised.exception))

    def test_a_lookup_can_be_pointed_at_a_different_set(self) -> None:
        only = (editions.EDITIONS[1],)

        self.assertIs(editions.named(only[0].name, among=only), only[0])
        self.assertIsNone(
            editions.matching(editions.EDITIONS[0].before[editions.DECIDES], among=only)
        )


if __name__ == "__main__":
    unittest.main()
