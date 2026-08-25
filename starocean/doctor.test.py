import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent / "snes-rom-image-python"))
sys.path.append(
    str(Path(__file__).resolve().parent.parent / "snes-rom-image-python" / "snes-mapper-python")
)

from starocean import doctor, editions


class Complaint(Exception):
    pass


def a_file(body: str) -> Path:
    where = Path(tempfile.mkdtemp()) / "held.json"
    where.write_text(body)
    return where


def refusing() -> Any:
    def refuse() -> Any:
        raise Complaint("no")

    return unittest.mock.patch.object(doctor, "_loaded", refuse)


class FindingTest(unittest.TestCase):
    def test_a_finding_says_what_was_checked(self) -> None:
        one = doctor.Finding("python", True, "3.14")

        self.assertEqual(one.name, "python")

    def test_a_healthy_finding_prints_with_a_mark_that_says_so(self) -> None:
        one = doctor.Finding("python", True, "3.14")

        self.assertIn("ok", one.line)

    def test_and_an_unhealthy_one_prints_differently(self) -> None:
        one = doctor.Finding("python", False, "3.9")

        self.assertNotIn("ok", one.line)

    def test_an_unhealthy_finding_says_what_to_do_about_it(self) -> None:
        one = doctor.Finding("python", False, "3.9", "upgrade")

        self.assertIn("upgrade", one.report)

    def test_a_healthy_one_keeps_its_advice_to_itself(self) -> None:
        one = doctor.Finding("python", True, "3.14", "upgrade")

        self.assertNotIn("upgrade", one.report)

    def test_and_so_does_an_unhealthy_one_with_none_to_give(self) -> None:
        one = doctor.Finding("python", False, "3.9")

        self.assertEqual(one.report, one.line)

    def test_a_finding_prints_as_itself(self) -> None:
        one = doctor.Finding("python", False, "3.9")

        self.assertEqual(repr(one), "<Finding python not ok>")

    def test_and_says_so_when_it_is_well(self) -> None:
        one = doctor.Finding("python", True, "3.14")

        self.assertEqual(repr(one), "<Finding python ok>")


class VersionTest(unittest.TestCase):
    def test_it_reports_the_python_it_is_running_on(self) -> None:
        one = doctor._python()

        self.assertTrue(one.ok, one.detail)

    def test_and_names_the_package(self) -> None:
        one = doctor._package()

        self.assertEqual(one.name, "starocean")

    def test_the_version_is_read_out_of_the_file_rather_than_imported(self) -> None:
        from starocean.version import VERSION

        self.assertEqual(doctor.VERSION, VERSION)

    def test_a_version_file_naming_nothing_reads_as_unknown(self) -> None:
        where = Path(tempfile.mkdtemp()) / "version.py"
        where.write_text("NOTHING = 1\n")

        self.assertEqual(doctor._version(where), "unknown")

    def test_the_repository_is_put_on_the_path_when_it_is_not_already_there(self) -> None:
        held = [one for one in sys.path if one != str(doctor.ROOT)]

        with unittest.mock.patch.object(sys, "path", held):
            doctor._loaded()

            self.assertIn(str(doctor.ROOT), held)


class EditionTest(unittest.TestCase):
    def test_every_edition_names_a_full_chain(self) -> None:
        one = doctor._editions()

        self.assertTrue(one.ok, one.detail)

    def test_and_each_of_them_appears_in_the_line(self) -> None:
        one = doctor._editions()

        self.assertTrue(all(held.name in one.detail for held in editions.EDITIONS), one.detail)

    def test_an_edition_with_a_link_missing_is_named(self) -> None:
        class Short:
            name = "shortened"
            size = 1

            def chain(self) -> tuple[Any, ...]:
                return ()

        with unittest.mock.patch.object(editions, "EDITIONS", (Short(),)):
            one = doctor._editions()

        self.assertIn("shortened", one.advice or "")

    def test_and_the_finding_is_not_well(self) -> None:
        class Short:
            name = "shortened"
            size = 1

            def chain(self) -> tuple[Any, ...]:
                return ()

        with unittest.mock.patch.object(editions, "EDITIONS", (Short(),)):
            one = doctor._editions()

        self.assertFalse(one.ok)

    def test_a_package_that_will_not_import_is_reported_as_what_it_said(self) -> None:
        with refusing():
            one = doctor._editions()

        self.assertIn("Complaint", one.detail)


class ChainTest(unittest.TestCase):
    def test_every_link_of_every_chain_gets_a_line(self) -> None:
        found = doctor._chain()
        wanted = sum(len(one.chain()) for one in editions.EDITIONS)

        self.assertEqual(len(found), wanted)

    def test_the_written_image_is_looked_for_where_it_is_written(self) -> None:
        found = [one for one in doctor._chain() if one.name.endswith(doctor.WRITES)]

        self.assertTrue(all(doctor.DESTINATION.name in one.detail for one in found), found)

    def test_and_every_other_link_where_it_is_read(self) -> None:
        found = [one for one in doctor._chain() if not one.name.endswith(doctor.WRITES)]

        self.assertTrue(all(doctor.SOURCE.name in one.detail for one in found), found)

    def test_a_file_that_is_not_there_is_said_to_be_absent(self) -> None:
        with unittest.mock.patch.object(doctor, "SOURCE", Path(tempfile.mkdtemp())):
            found = doctor._chain()

        self.assertTrue(any("is not at" in one.detail for one in found))

    def test_a_package_that_will_not_import_reports_no_chain_at_all(self) -> None:
        with refusing():
            found = doctor._chain()

        self.assertEqual(found, [])


class SubmoduleTest(unittest.TestCase):
    def test_every_submodule_this_repository_carries_is_checked_out(self) -> None:
        absent = [name for name in doctor.SUBMODULES if not doctor._submodule(name).ok]

        self.assertEqual(absent, [])

    def test_a_submodule_that_is_not_there_is_reported(self) -> None:
        one = doctor._submodule("absent", Path(tempfile.mkdtemp()))

        self.assertIn("is not there", one.detail)

    def test_a_directory_git_left_empty_is_reported_as_empty(self) -> None:
        where = Path(tempfile.mkdtemp())
        (where / "hollow").mkdir()

        one = doctor._submodule("hollow", where)

        self.assertIn("is empty", one.detail)

    def test_and_neither_is_well_because_nothing_here_runs_without_it(self) -> None:
        one = doctor._submodule("absent", Path(tempfile.mkdtemp()))

        self.assertFalse(one.ok)


class ManifestTest(unittest.TestCase):
    def test_the_manifest_beside_the_package_pins_editions(self) -> None:
        one = doctor._manifest()

        self.assertTrue(one.ok, one.detail)

    def test_and_records_the_outputs_a_previous_correction_produced(self) -> None:
        one = doctor._manifest()

        self.assertIn("superseded", one.detail)

    def test_a_manifest_that_is_not_there_is_reported(self) -> None:
        one = doctor._manifest(Path(tempfile.mkdtemp()) / "absent.json")

        self.assertFalse(one.ok)

    def test_a_manifest_that_is_not_json_is_reported_differently(self) -> None:
        one = doctor._manifest(a_file("{"))

        self.assertIn("not readable as JSON", one.detail)

    def test_a_manifest_pinning_nothing_is_not_well(self) -> None:
        one = doctor._manifest(a_file('{"editions": []}'))

        self.assertFalse(one.ok)

    def test_a_manifest_with_no_superseded_digests_says_that_rather_than_nothing(self) -> None:
        one = doctor._manifest(a_file(json.dumps({"editions": [{"name": "one"}]})))

        self.assertIn("none carrying superseded digests", one.detail)


class SourceTest(unittest.TestCase):
    def test_a_directory_of_images_is_counted(self) -> None:
        where = Path(tempfile.mkdtemp())
        (where / "one.sfc").write_bytes(b"\x00")

        one = doctor._source(where)

        self.assertIn("1 files", one.detail)

    def test_a_directory_that_is_not_there_is_reported_as_nothing_to_do(self) -> None:
        one = doctor._source(Path(tempfile.mkdtemp()) / "absent")

        self.assertIn("nothing to correct", one.detail)

    def test_and_is_not_a_fault_because_a_fresh_checkout_has_none(self) -> None:
        one = doctor._source(Path(tempfile.mkdtemp()) / "absent")

        self.assertTrue(one.ok)

    def test_an_empty_directory_says_so_too(self) -> None:
        one = doctor._source(Path(tempfile.mkdtemp()))

        self.assertIn("empty", one.detail)

    def test_a_directory_that_cannot_be_read_is_reported_as_what_it_said(self) -> None:
        def refuse(*_: Any, **__: Any) -> Any:
            raise OSError("permission denied")

        with unittest.mock.patch.object(Path, "iterdir", refuse):
            one = doctor._source(Path(tempfile.mkdtemp()))

        self.assertIn("permission denied", one.detail)


class ExamineTest(unittest.TestCase):
    def test_the_examination_produces_findings(self) -> None:
        found = doctor.examine()

        self.assertTrue(all(isinstance(one, doctor.Finding) for one in found))

    def test_it_looks_at_every_submodule_this_repository_carries(self) -> None:
        named = {one.name for one in doctor.examine()}

        self.assertTrue({f"submodule {name}" for name in doctor.SUBMODULES} <= named, named)

    def test_and_nothing_it_looks_at_is_unwell_on_this_machine(self) -> None:
        unwell = [one.name for one in doctor.examine() if not one.ok]

        self.assertEqual(unwell, [])


class ReportTest(unittest.TestCase):
    def test_a_clean_examination_says_there_is_nothing_to_report(self) -> None:
        lines = doctor.report([doctor.Finding("one", True, "fine")])

        self.assertIn("nothing to report", lines[-1])

    def test_and_a_dirty_one_counts_what_did_not_pass(self) -> None:
        lines = doctor.report(
            [doctor.Finding("one", True, "fine"), doctor.Finding("two", False, "not")]
        )

        self.assertIn("1 of 2", lines[-1])


class MainTest(unittest.TestCase):
    def test_a_clean_machine_exits_zero(self) -> None:
        code = doctor.main((), lambda: [doctor.Finding("one", True, "fine")], lambda _: None)

        self.assertEqual(code, 0)

    def test_and_a_machine_with_a_finding_exits_one(self) -> None:
        code = doctor.main((), lambda: [doctor.Finding("one", False, "not")], lambda _: None)

        self.assertEqual(code, 1)

    def test_the_report_is_said_rather_than_returned(self) -> None:
        said: list[str] = []

        doctor.main((), lambda: [doctor.Finding("one", True, "fine")], said.append)

        self.assertTrue(any("nothing to report" in one for one in said))

    def test_it_runs_end_to_end_whatever_this_machine_holds(self) -> None:
        """A report, not a verdict that the machine is well.

        Asserting a clean exit here would make the suite require exactly the
        machine the doctor exists to report on. CI has no cartridges, and a
        doctor that says so is working. What has to hold on every machine is
        that it examines everything and prints a line for each finding.
        """
        said: list[str] = []

        code = doctor.main((), doctor.examine, said.append)

        self.assertIn(code, (0, 1))
        self.assertGreaterEqual(len(said), len(doctor.examine()))


if __name__ == "__main__":
    unittest.main()
