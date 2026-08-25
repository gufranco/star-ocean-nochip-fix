import hashlib
import sys
import tempfile
import unittest
import unittest.mock
import zlib
from pathlib import Path
from typing import Any, override

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starocean import editions, fix
from starocean.errors import Corrupt, Missing, NotACartridge, Unexpected, Unrecognised


def an_image(
    size: int = 0x100000, chipset: int = 0x45, declared: int = 0x0D, at: int = 0x7FC0
) -> bytes:
    rom = bytearray(size)
    rom[at : at + 21] = b"Star Ocean           "
    rom[at + 21] = 0x32
    rom[at + 22] = chipset
    rom[at + 23] = declared
    rom[at + 25] = 0x00
    rom[at + 28] = 0xA5
    rom[at + 29] = 0xA5
    rom[at + 30] = 0x5A
    rom[at + 31] = 0x5A
    return bytes(rom)


def digests_of(blob: bytes) -> dict[str, str]:
    return {
        "crc32": f"{zlib.crc32(blob) & 0xFFFFFFFF:08x}",
        "md5": hashlib.md5(blob).hexdigest(),
        "sha1": hashlib.sha1(blob).hexdigest(),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def a_link(blob: bytes, name: str) -> dict[str, Any]:
    return dict(digests_of(blob), bytes=len(blob), name=name)


def an_edition(
    before: bytes, after: bytes, name: str = "made-up", size: int = 0x100000
) -> editions.Edition:
    return editions.Edition(
        name=name,
        summary="a stand-in",
        reads="in.sfc",
        writes="out.sfc",
        size=size,
        before=digests_of(before),
        after=digests_of(after),
        source=a_link(b"a cartridge" * 8, "cartridge.sfc"),
        patch=a_link(b"a patch" * 8, "patch.xdelta"),
    )


class DigestTest(unittest.TestCase):
    def test_all_four_digests_are_computed(self) -> None:
        found = fix.digests_of(b"anything")

        self.assertEqual(set(found), set(editions.DIGESTS))

    def test_each_is_the_length_that_kind_of_digest_has(self) -> None:
        found = fix.digests_of(b"anything")

        for name, width in editions.DIGEST_WIDTHS.items():
            self.assertEqual(len(found[name]), width)

    def test_the_same_bytes_always_give_the_same_digests(self) -> None:
        self.assertEqual(fix.digests_of(b"abc"), fix.digests_of(b"abc"))


class CorrectTest(unittest.TestCase):
    def test_the_coprocessor_claim_is_cleared(self) -> None:
        corrected = fix.correct(an_image())

        self.assertEqual(corrected[0x7FC0 + 22], 0x00)

    def test_the_declared_size_is_made_to_match_the_file(self) -> None:
        corrected = fix.correct(an_image(size=0x100000, declared=0x0D))

        self.assertEqual(corrected[0x7FC0 + 23], 0x0A)

    def test_the_checksum_is_recomputed_over_the_result(self) -> None:
        corrected = fix.correct(an_image())

        low = corrected[0x7FC0 + 30] | (corrected[0x7FC0 + 31] << 8)
        complement = corrected[0x7FC0 + 28] | (corrected[0x7FC0 + 29] << 8)
        self.assertEqual(low ^ complement, 0xFFFF)

    def test_an_image_needing_nothing_comes_back_unchanged(self) -> None:
        already = fix.correct(an_image(chipset=0x00, declared=0x0A))

        self.assertEqual(fix.correct(already), already)

    def test_correcting_twice_changes_nothing_the_second_time(self) -> None:
        once = fix.correct(an_image())

        self.assertEqual(fix.correct(once), once)

    def test_an_image_with_no_header_is_refused(self) -> None:
        with self.assertRaises(NotACartridge):
            fix.correct(bytes(0x100000))


class ConfirmTest(unittest.TestCase):
    def test_an_image_the_manifest_knows_is_accepted(self) -> None:
        before = an_image()
        edition = an_edition(before, fix.correct(before))

        self.assertIs(fix.confirm(before, edition), edition)

    def test_an_image_of_the_wrong_length_is_refused_before_it_is_hashed(self) -> None:
        before = an_image()
        edition = an_edition(before, fix.correct(before), size=0x200000)

        with self.assertRaises(Unrecognised) as raised:
            fix.confirm(before, edition)

        self.assertIn("bytes", str(raised.exception))

    def test_an_image_of_the_right_length_and_wrong_content_is_refused(self) -> None:
        before = an_image()
        edition = an_edition(an_image(declared=0x0B), fix.correct(before))

        with self.assertRaises(Unrecognised) as raised:
            fix.confirm(before, edition)

        self.assertIn("sha256", str(raised.exception))

    def test_a_manifest_that_disagrees_with_itself_is_reported_as_that(self) -> None:
        before = an_image()
        edition = an_edition(before, fix.correct(before))
        edition.before = dict(edition.before, crc32="00000000")

        with self.assertRaises(Corrupt) as raised:
            fix.confirm(before, edition)

        self.assertIn("crc32", str(raised.exception))

    def test_every_kind_of_disagreement_is_caught(self) -> None:
        before = an_image()
        for name, wrong in (("md5", "0" * 32), ("sha1", "0" * 40), ("crc32", "0" * 8)):
            edition = an_edition(before, fix.correct(before))
            edition.before = dict(edition.before, **{name: wrong})

            with self.assertRaises(Corrupt):
                fix.confirm(before, edition)


class ApplyTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.before = an_image()
        self.after = fix.correct(self.before)
        self.edition = an_edition(self.before, self.after)

    def test_the_corrected_image_comes_back(self) -> None:
        self.assertEqual(fix.apply(self.before, self.edition), self.after)

    def test_a_result_the_manifest_did_not_predict_is_refused(self) -> None:
        wrong = an_edition(self.before, an_image(declared=0x0C))

        with self.assertRaises(Unexpected) as raised:
            fix.apply(self.before, wrong)

        self.assertIn("sha256", str(raised.exception))

    def test_the_refusal_names_what_was_produced_so_it_can_be_looked_up(self) -> None:
        wrong = an_edition(self.before, an_image(declared=0x0C))

        with self.assertRaises(Unexpected) as raised:
            fix.apply(self.before, wrong)

        self.assertIn(fix.digests_of(self.after)["sha256"], str(raised.exception))

    def test_an_image_that_is_not_the_one_named_never_reaches_the_correction(self) -> None:
        other = an_edition(an_image(declared=0x0B), self.after)

        with self.assertRaises(Unrecognised):
            fix.apply(self.before, other)


class OnDiskTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.where = Path(tempfile.mkdtemp())
        self.before = an_image()
        self.edition = an_edition(self.before, fix.correct(self.before))
        (self.where / self.edition.reads).write_bytes(self.before)

    def test_a_corrected_file_is_written_beside_the_one_it_came_from(self) -> None:
        written = fix.run(self.edition, self.where, self.where)

        self.assertEqual(written.read_bytes(), fix.correct(self.before))

    def test_the_written_file_carries_the_name_the_manifest_gives_it(self) -> None:
        written = fix.run(self.edition, self.where, self.where)

        self.assertEqual(written.name, self.edition.writes)

    def test_a_source_that_is_not_there_is_refused(self) -> None:
        with self.assertRaises(Missing) as raised:
            fix.run(self.edition, Path("/nowhere/at/all"), self.where)

        self.assertIn(self.edition.reads, str(raised.exception))

    def test_running_twice_writes_the_same_file(self) -> None:
        once = fix.run(self.edition, self.where, self.where).read_bytes()

        self.assertEqual(fix.run(self.edition, self.where, self.where).read_bytes(), once)

    def test_a_destination_that_does_not_exist_yet_is_created(self) -> None:
        into = self.where / "made" / "up"

        written = fix.run(self.edition, self.where, into)

        self.assertTrue(written.is_file())


class SourceDirectoryTest(unittest.TestCase):
    def test_the_directory_comes_from_the_environment_when_one_is_named(self) -> None:
        self.assertEqual(fix.source_directory({fix.DIRECTORY_VARIABLE: "/x"}), Path("/x"))

    def test_a_named_directory_wins_even_when_it_is_not_there(self) -> None:
        self.assertEqual(
            fix.source_directory({fix.DIRECTORY_VARIABLE: "/nowhere"}), Path("/nowhere")
        )

    def test_and_the_folder_in_this_repository_is_used_when_none_is(self) -> None:
        self.assertEqual(fix.source_directory({}), fix.DEFAULT_SOURCE)

    def test_the_project_this_sits_inside_is_looked_at_too(self) -> None:
        self.assertIn(fix.ALONGSIDE, fix.source_directories({}))

    def test_a_named_directory_comes_before_either_of_them(self) -> None:
        found = fix.source_directories({fix.DIRECTORY_VARIABLE: "/x"})

        self.assertEqual(found[0], Path("/x"))

    def test_the_first_place_that_is_actually_there_is_the_one_used(self) -> None:
        import tempfile

        here = Path(tempfile.mkdtemp())

        self.assertEqual(fix.source_directory({}, places=[Path("/nowhere"), here]), here)

    def test_and_when_no_place_is_there_the_folder_here_is_named(self) -> None:
        chosen = fix.source_directory({}, places=[Path("/nowhere"), Path("/nor/here")])

        self.assertEqual(chosen, fix.DEFAULT_SOURCE)


class MainTest(unittest.TestCase):
    @override
    def setUp(self) -> None:
        self.where = Path(tempfile.mkdtemp())

    def test_a_directory_with_neither_image_reports_that_nothing_was_done(self) -> None:
        self.assertEqual(fix.main([str(self.where), str(self.where)]), 2)

    def test_a_file_under_the_right_name_but_the_wrong_content_is_refused(self) -> None:
        edition = editions.EDITIONS[0]
        (self.where / edition.reads).write_bytes(an_image(size=edition.size))

        self.assertEqual(fix.main([str(self.where), str(self.where / "out")]), 1)

    def test_a_refusal_writes_nothing(self) -> None:
        edition = editions.EDITIONS[0]
        (self.where / edition.reads).write_bytes(an_image(size=edition.size))
        into = self.where / "out"

        fix.main([str(self.where), str(into)])

        self.assertFalse((into / edition.writes).exists())

    def test_a_file_with_no_header_at_all_is_refused_rather_than_crashing(self) -> None:
        edition = editions.EDITIONS[0]
        (self.where / edition.reads).write_bytes(bytes(edition.size))

        self.assertEqual(fix.main([str(self.where), str(self.where / "out")]), 1)

    def test_one_argument_uses_the_destination_in_this_repository(self) -> None:
        self.assertEqual(fix.main([str(self.where)]), 2)

    def test_an_image_it_recognises_is_corrected_and_reported(self) -> None:
        before = an_image()
        edition = an_edition(before, fix.correct(before))
        (self.where / edition.reads).write_bytes(before)
        into = self.where / "out"

        self.assertEqual(fix.main([str(self.where), str(into)], catalogue=(edition,)), 0)
        self.assertEqual((into / edition.writes).read_bytes(), fix.correct(before))

    def test_one_present_and_one_absent_still_corrects_the_one_that_is_here(self) -> None:
        before = an_image()
        here = an_edition(before, fix.correct(before), name="here")
        absent = an_edition(before, fix.correct(before), name="absent")
        absent.reads = "not-here.sfc"
        (self.where / here.reads).write_bytes(before)

        self.assertEqual(fix.main([str(self.where), str(self.where / "out")], (here, absent)), 0)


class CommandTest(unittest.TestCase):
    """The installed console command, which is the only caller of sys.argv here.

    It exists so that a shell can run this without knowing the module layout, and
    it is one line, and that line is the difference between exiting with what the
    run decided and exiting with zero regardless.
    """

    def test_it_exits_with_what_the_run_decided(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            argv = [sys.argv[0], empty, empty]
            with (
                unittest.mock.patch.object(sys, "argv", argv),
                self.assertRaises(SystemExit) as held,
            ):
                fix.command()

        self.assertEqual(held.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
