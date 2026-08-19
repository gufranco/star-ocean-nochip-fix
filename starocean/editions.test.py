import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starocean import editions


class CatalogueTest(unittest.TestCase):
    def test_both_editions_are_listed(self):
        self.assertEqual(len(editions.EDITIONS), 2)

    def test_each_edition_has_a_name_of_its_own(self):
        names = [edition.name for edition in editions.EDITIONS]

        self.assertEqual(len(names), len(set(names)))

    def test_each_edition_names_the_file_it_reads_and_the_file_it_writes(self):
        for edition in editions.EDITIONS:
            self.assertTrue(edition.reads)
            self.assertTrue(edition.writes)
            self.assertNotEqual(edition.reads, edition.writes)

    def test_both_editions_are_the_same_length(self):
        lengths = {edition.size for edition in editions.EDITIONS}

        self.assertEqual(lengths, {editions.EXPECTED_BYTES})

    def test_that_length_is_the_one_the_whole_bank_map_has(self):
        self.assertEqual(editions.EXPECTED_BYTES, 0xC00000)

    def test_an_edition_prints_as_its_name_and_length(self):
        printed = repr(editions.EDITIONS[0])

        self.assertIn(editions.EDITIONS[0].name, printed)
        self.assertIn(str(editions.EDITIONS[0].size), printed)

    def test_the_table_is_read_from_the_manifest_rather_than_written_in_code(self):
        self.assertTrue(editions.MANIFEST.is_file())
        self.assertEqual(len(editions.load()), len(editions.EDITIONS))

    def test_a_manifest_somewhere_else_can_be_read_instead(self):
        import json
        import tempfile

        where = Path(tempfile.mkdtemp()) / "other.json"
        where.write_text(json.dumps({"editions": []}))

        self.assertEqual(editions.load(where), ())


class DigestTest(unittest.TestCase):
    def test_every_edition_pins_all_four_digests_of_what_it_reads(self):
        for edition in editions.EDITIONS:
            for name, width in editions.DIGEST_WIDTHS.items():
                self.assertEqual(len(edition.before[name]), width, (edition.name, name))

    def test_and_all_four_of_what_it_writes(self):
        for edition in editions.EDITIONS:
            for name, width in editions.DIGEST_WIDTHS.items():
                self.assertEqual(len(edition.after[name]), width, (edition.name, name))

    def test_no_edition_reads_and_writes_the_same_bytes(self):
        for edition in editions.EDITIONS:
            self.assertNotEqual(edition.before[editions.DECIDES], edition.after[editions.DECIDES])

    def test_no_two_editions_share_a_deciding_digest(self):
        seen = [edition.before[editions.DECIDES] for edition in editions.EDITIONS]
        seen += [edition.after[editions.DECIDES] for edition in editions.EDITIONS]

        self.assertEqual(len(seen), len(set(seen)))

    def test_every_digest_is_written_in_lower_case_hexadecimal(self):
        for edition in editions.EDITIONS:
            for held in (edition.before, edition.after):
                for value in held.values():
                    self.assertRegex(value, r"^[0-9a-f]+$")


class LookupTest(unittest.TestCase):
    def test_an_edition_is_found_by_the_digest_of_what_it_reads(self):
        wanted = editions.EDITIONS[0]

        self.assertIs(editions.matching(wanted.before[editions.DECIDES]), wanted)

    def test_a_digest_no_edition_carries_finds_nothing(self):
        self.assertIsNone(editions.matching("0" * 64))

    def test_an_edition_is_found_by_name(self):
        wanted = editions.EDITIONS[0]

        self.assertIs(editions.named(wanted.name), wanted)

    def test_a_name_no_edition_carries_is_refused(self):
        with self.assertRaises(editions.UnknownEdition):
            editions.named("nonsense")

    def test_the_refusal_lists_the_editions_there_are(self):
        with self.assertRaises(editions.UnknownEdition) as raised:
            editions.named("nonsense")

        for edition in editions.EDITIONS:
            self.assertIn(edition.name, str(raised.exception))

    def test_a_lookup_can_be_pointed_at_a_different_set(self):
        only = (editions.EDITIONS[1],)

        self.assertIs(editions.named(only[0].name, among=only), only[0])
        self.assertIsNone(
            editions.matching(editions.EDITIONS[0].before[editions.DECIDES], among=only)
        )


if __name__ == "__main__":
    unittest.main()
