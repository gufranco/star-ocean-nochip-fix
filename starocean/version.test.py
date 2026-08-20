import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starocean import version


class VersionTest(unittest.TestCase):
    def test_a_version_is_recorded(self) -> None:
        self.assertTrue(version.VERSION)

    def test_it_reads_as_three_numbers(self) -> None:
        self.assertRegex(version.VERSION, r"^\d+\.\d+\.\d+([-+].*)?$")

    def test_the_release_script_writes_the_field_this_file_holds(self) -> None:
        script = (Path(__file__).resolve().parent.parent / "scripts" / "set-version.sh").read_text()

        self.assertIn("starocean/version.py", script)

    def test_nothing_else_in_the_package_carries_a_version_of_its_own(self) -> None:
        package = Path(__file__).resolve().parent
        elsewhere = [
            path.name
            for path in package.glob("*.py")
            if path.name != "version.py" and re.search(r"^VERSION = ", path.read_text(), re.M)
        ]

        self.assertEqual(elsewhere, [])


if __name__ == "__main__":
    unittest.main()
