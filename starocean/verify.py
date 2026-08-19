"""Say what is on disk and whether it is what it claims, and write nothing.

Running the correction to find out whether your files are right costs a read and
a write of twelve megabytes each, and leaves a file behind whether or not you
wanted one. This answers the same question by reading only.

It looks for every step of the chain rather than only the image the correction
consumes, because "this is not the one named" is an unhelpful thing to be told
when the real answer is that the wrong patch was applied two steps earlier. A
report naming which link is wrong points at the step to redo.

Four states, and the difference between the middle two is the point. A file the
manifest does not recognise at all was built from something else. A file matching
the deciding digest but not the rest means the manifest disagrees with itself,
which is a defect here rather than in anybody's copy.
"""

import hashlib
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))

from starocean import editions

ABSENT = "absent"
MATCHES = "matches"
ALTERED = "altered"
CORRUPT = "corrupt"

NOTHING = "nothing"
SOUND = "sound"
WRONG = "wrong"

DEFAULT_SOURCE = ROOT / "roms"

DEFAULT_DESTINATION = ROOT / "dist"

SHOWN = 16
"""How much of a computed digest a report prints: enough to search for."""


class Finding:
    """One step of one edition, and what was found where it belongs."""

    def __init__(self, edition, step, path, state, found=None):
        self.edition = edition
        self.step = step
        self.path = path
        self.state = state
        self.found = found

    def __repr__(self):
        return f"<{self.state} {self.step.name}>"


def digests_of(image):
    return {
        "crc32": f"{zlib.crc32(image) & 0xFFFFFFFF:08x}",
        "md5": hashlib.md5(image).hexdigest(),
        "sha1": hashlib.sha1(image).hexdigest(),
        "sha256": hashlib.sha256(image).hexdigest(),
    }


def _somewhere_under(where, name):
    """The named file directly in a directory, or anywhere beneath it."""
    direct = Path(where) / name
    if direct.is_file() or not Path(where).is_dir():
        return direct
    for path in sorted(Path(where).rglob(name)):
        if path.is_file():
            return path
    return direct


def _state_of(image, held):
    found = digests_of(image)
    if found[editions.DECIDES] != held[editions.DECIDES]:
        return ALTERED, found
    for digest in editions.DIGESTS:
        if digest in held and held[digest].lower() != found[digest]:
            return CORRUPT, found
    return MATCHES, found


def look(source=None, catalogue=None, destination=None):
    """Every step of every edition, and what sits where it belongs."""
    source = DEFAULT_SOURCE if source is None else Path(source)
    destination = DEFAULT_DESTINATION if destination is None else Path(destination)
    catalogue = editions.EDITIONS if catalogue is None else catalogue

    findings = []
    for edition in catalogue:
        for step in edition.chain():
            where = destination if step.produced else source
            path = _somewhere_under(where, step.name)
            if not path.is_file():
                findings.append(Finding(edition, step, path, ABSENT))
                continue
            state, found = _state_of(path.read_bytes(), step.held)
            findings.append(Finding(edition, step, path, state, found))
    return findings


def report(findings):
    """One line per finding, in the words a person reads."""
    lines = []
    for one in findings:
        line = f"  {one.edition.name}: {one.step.what} {one.state}, {one.step.name}"
        if one.state in (ALTERED, CORRUPT):
            line += f" (found {one.found[editions.DECIDES][:SHOWN]})"
        lines.append(line)
    return lines


def verdict(findings):
    """Whether what is here is sound, wrong, or not here at all."""
    if any(one.state in (ALTERED, CORRUPT) for one in findings):
        return WRONG
    if any(one.state == MATCHES for one in findings):
        return SOUND
    return NOTHING


def main(argv, catalogue=None):
    source = Path(argv[0]) if argv else DEFAULT_SOURCE
    destination = Path(argv[1]) if len(argv) > 1 else DEFAULT_DESTINATION

    findings = look(source, catalogue, destination)
    for line in report(findings):
        print(line)

    told = verdict(findings)
    if told == WRONG:
        print("  something here is not what the manifest says it is")
        return 1
    if told == NOTHING:
        print(f"  nothing from the chain was found under {source}")
        return 2
    print("  everything found matches what the manifest says")
    return 0


def command():
    """The installed console command, which takes its arguments from the shell."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    command()
