"""The two images this corrects, named, and pinned at both ends.

Star Ocean shipped on an S-DD1 board, which decompressed graphics on the way to
the console. Somebody else did the work of decompressing all of it ahead of time
and rebuilding the cartridge at ninety six megabit, so the chip is no longer doing
anything. Two of those rebuilds exist, one Japanese and one carrying the English
translation, and both still say in their header that an S-DD1 is fitted.

The header is also short by a size: both declare eight megabytes while being
twelve. That was already wrong before anyone touched the file, because the field
holds a power of two and there is no power of two at twelve.

Neither rebuild is work anyone should redo. The correction is six bytes per header
mirror, and what is pinned is the whole result: four digests of the image that goes
in and four of the image that comes out. A run producing anything else has done
something other than what this describes, and says so rather than writing.

The table itself is data rather than code. Filenames and digests are the two things
most likely to need a correction of their own, and a table nobody has to read
Python to check is easier to correct.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MANIFEST = ROOT / "roms.manifest.json"

DIGESTS = ("crc32", "md5", "sha1", "sha256")

DECIDES = "sha256"

DIGEST_WIDTHS = {"crc32": 8, "md5": 32, "sha1": 40, "sha256": 64}

EXPECTED_BYTES = 0xC00000
"""Twelve megabytes.

Both rebuilds are exactly this, and the map they use has no other size: its window
only sits inside the file at 192 banks.
"""


class UnknownEdition(Exception):
    pass


class Edition:
    """One rebuild: what it is, what it is read from, and what it becomes."""

    def __init__(self, name, summary, reads, writes, size, before, after):
        self.name = name
        self.summary = summary
        self.reads = reads
        self.writes = writes
        self.size = size
        self.before = before
        self.after = after

    def __repr__(self):
        return f"<Edition {self.name}, {self.size} bytes>"


def load(path=None):
    """Every edition the manifest lists, in the order it lists them."""
    with Path(path or MANIFEST).open() as handle:
        held = json.load(handle)
    return tuple(
        Edition(
            name=entry["name"],
            summary=entry["summary"],
            reads=entry["reads"],
            writes=entry["writes"],
            size=entry["bytes"],
            before=entry["before"],
            after=entry["after"],
        )
        for entry in held["editions"]
    )


EDITIONS = load()


def matching(digest, among=None):
    """The edition an image with that deciding digest is, or nothing."""
    for edition in EDITIONS if among is None else among:
        if edition.before[DECIDES] == digest:
            return edition
    return None


def named(name, among=None):
    """The edition of that name."""
    among = EDITIONS if among is None else among
    for edition in among:
        if edition.name == name:
            return edition
    raise UnknownEdition(
        f"{name} is not an edition this corrects;"
        f" there are {', '.join(edition.name for edition in among)}"
    )
