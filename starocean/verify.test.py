import hashlib
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starocean import editions, verify


def digests_of(blob):
    return {
        "bytes": len(blob),
        "crc32": f"{zlib.crc32(blob) & 0xFFFFFFFF:08x}",
        "md5": hashlib.md5(blob).hexdigest(),
        "sha1": hashlib.sha1(blob).hexdigest(),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def an_edition(name="made-up", **files):
    held = {what: digests_of(blob) for what, blob in files.items()}
    return editions.Edition(
        name=name,
        summary="a stand-in",
        reads="reads.sfc",
        writes="writes.sfc",
        size=held["reads"]["bytes"],
        before={k: v for k, v in held["reads"].items() if k != "bytes"},
        after={k: v for k, v in held["writes"].items() if k != "bytes"},
        source=dict(held["source"], name="source.sfc"),
        patch=dict(held["patch"], name="patch.xdelta"),
    )


SOURCE = b"a cartridge" * 40
PATCH = b"a patch" * 30
READS = b"the patched image" * 20
WRITES = b"the corrected image" * 20

EDITION = an_edition(source=SOURCE, patch=PATCH, reads=READS, writes=WRITES)


class StateTest(unittest.TestCase):
    def setUp(self):
        self.where = Path(tempfile.mkdtemp())

    def test_a_file_that_is_not_there_is_reported_as_absent(self):
        found = verify.look(self.where, (EDITION,))

        self.assertTrue(all(one.state == verify.ABSENT for one in found))

    def test_a_file_that_matches_is_reported_as_matching(self):
        (self.where / "reads.sfc").write_bytes(READS)

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,))}

        self.assertEqual(found["reads"], verify.MATCHES)

    def test_a_file_of_the_right_length_and_wrong_content_is_altered(self):
        (self.where / "reads.sfc").write_bytes(bytes(len(READS)))

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,))}

        self.assertEqual(found["reads"], verify.ALTERED)

    def test_a_file_of_the_wrong_length_is_altered_too(self):
        (self.where / "reads.sfc").write_bytes(b"short")

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,))}

        self.assertEqual(found["reads"], verify.ALTERED)

    def test_a_file_matching_on_the_deciding_digest_but_not_the_rest_is_corrupt(self):
        edition = an_edition(source=SOURCE, patch=PATCH, reads=READS, writes=WRITES)
        edition.before = dict(edition.before, crc32="00000000")
        (self.where / "reads.sfc").write_bytes(READS)

        found = {one.step.what: one.state for one in verify.look(self.where, (edition,))}

        self.assertEqual(found["reads"], verify.CORRUPT)

    def test_every_step_of_the_chain_is_looked_for(self):
        found = verify.look(self.where, (EDITION,))

        self.assertEqual([one.step.what for one in found], ["source", "patch", "reads", "writes"])

    def test_the_place_a_file_was_looked_for_is_reported(self):
        into = self.where / "out"

        found = verify.look(self.where, (EDITION,), into)

        for one in found:
            wanted = into if one.step.produced else self.where
            self.assertEqual(one.path.parent, wanted, one.step.what)

    def test_a_file_this_repository_makes_is_never_looked_for_among_the_sources(self):
        into = self.where / "out"
        (self.where / "writes.sfc").write_bytes(WRITES)

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,), into)}

        self.assertEqual(found["writes"], verify.ABSENT)

    def test_a_produced_file_is_looked_for_where_it_would_be_written(self):
        into = self.where / "out"
        into.mkdir()
        (into / "writes.sfc").write_bytes(WRITES)

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,), into)}

        self.assertEqual(found["writes"], verify.MATCHES)

    def test_a_directory_beneath_holding_something_else_is_walked_past(self):
        (self.where / "deep").mkdir()
        (self.where / "deep" / "reads.sfc").mkdir()

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,))}

        self.assertEqual(found["reads"], verify.ABSENT)

    def test_a_subdirectory_is_searched_as_well(self):
        (self.where / "somewhere").mkdir()
        (self.where / "somewhere" / "reads.sfc").write_bytes(READS)

        found = {one.step.what: one.state for one in verify.look(self.where, (EDITION,))}

        self.assertEqual(found["reads"], verify.MATCHES)

    def test_a_finding_prints_as_its_state_and_what_it_names(self):
        printed = repr(verify.look(self.where, (EDITION,))[0])

        self.assertIn(verify.ABSENT, printed)
        self.assertIn("source.sfc", printed)


class ReportTest(unittest.TestCase):
    def setUp(self):
        self.where = Path(tempfile.mkdtemp())

    def test_every_finding_makes_a_line(self):
        found = verify.look(self.where, (EDITION,))

        self.assertEqual(len(verify.report(found)), len(found))

    def test_a_line_names_the_edition_the_step_and_the_state(self):
        line = verify.report(verify.look(self.where, (EDITION,)))[0]

        self.assertIn("made-up", line)
        self.assertIn("source", line)
        self.assertIn(verify.ABSENT, line)

    def test_an_altered_file_says_what_was_computed_so_it_can_be_looked_up(self):
        (self.where / "reads.sfc").write_bytes(bytes(len(READS)))

        lines = [
            line
            for line in verify.report(verify.look(self.where, (EDITION,)))
            if verify.ALTERED in line
        ]

        self.assertIn(hashlib.sha256(bytes(len(READS))).hexdigest()[:16], lines[0])


class VerdictTest(unittest.TestCase):
    def setUp(self):
        self.where = Path(tempfile.mkdtemp())

    def test_nothing_present_is_neither_pass_nor_fail(self):
        self.assertEqual(verify.verdict(verify.look(self.where, (EDITION,))), verify.NOTHING)

    def test_everything_present_and_matching_passes(self):
        for name, blob in (
            ("source.sfc", SOURCE),
            ("patch.xdelta", PATCH),
            ("reads.sfc", READS),
            ("writes.sfc", WRITES),
        ):
            (self.where / name).write_bytes(blob)

        self.assertEqual(verify.verdict(verify.look(self.where, (EDITION,))), verify.SOUND)

    def test_one_file_present_and_matching_still_passes(self):
        (self.where / "reads.sfc").write_bytes(READS)

        self.assertEqual(verify.verdict(verify.look(self.where, (EDITION,))), verify.SOUND)

    def test_one_altered_file_fails_whatever_else_is_right(self):
        (self.where / "reads.sfc").write_bytes(READS)
        (self.where / "source.sfc").write_bytes(b"not the cartridge")

        self.assertEqual(verify.verdict(verify.look(self.where, (EDITION,))), verify.WRONG)


class MainTest(unittest.TestCase):
    def setUp(self):
        self.where = Path(tempfile.mkdtemp())

    def test_an_empty_directory_reports_that_nothing_was_found(self):
        self.assertEqual(verify.main([str(self.where)], (EDITION,)), 2)

    def test_a_directory_where_everything_matches_reports_success(self):
        (self.where / "reads.sfc").write_bytes(READS)

        self.assertEqual(verify.main([str(self.where)], (EDITION,)), 0)

    def test_a_directory_with_an_altered_file_reports_failure(self):
        (self.where / "reads.sfc").write_bytes(bytes(len(READS)))

        self.assertEqual(verify.main([str(self.where)], (EDITION,)), 1)

    def test_it_writes_nothing_whatever_it_finds(self):
        (self.where / "reads.sfc").write_bytes(READS)
        before = sorted(path.name for path in self.where.iterdir())

        verify.main([str(self.where)], (EDITION,))

        self.assertEqual(sorted(path.name for path in self.where.iterdir()), before)

    def test_no_arguments_reads_the_directories_in_this_repository(self):
        self.assertIn(verify.main([], (EDITION,)), (0, 1, 2))

    def test_a_second_argument_names_where_produced_files_are_looked_for(self):
        into = self.where / "out"
        into.mkdir()
        (into / "writes.sfc").write_bytes(WRITES)

        self.assertEqual(verify.main([str(self.where), str(into)], (EDITION,)), 0)


if __name__ == "__main__":
    unittest.main()
