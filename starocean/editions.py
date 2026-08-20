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
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, override

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


class Patch:
    """The hack the two images are built with, and where to find it."""

    def __init__(
        self,
        name: str,
        version: str,
        author: str,
        where: str,
        note: str,
        archive: Mapping[str, Any],
    ) -> None:
        self.name = name
        self.version = version
        self.author = author
        self.where = where
        self.note = note
        self.archive = archive

    @override
    def __repr__(self) -> str:
        return f"<Patch {self.name} {self.version}, by {self.author}>"


class Step:
    """One file in the chain, and whether this repository is what makes it."""

    def __init__(
        self, what: str, name: str, held: Mapping[str, Any], produced: bool = False
    ) -> None:
        self.what = what
        self.name = name
        self.held = held
        self.produced = produced

    @property
    def bytes(self) -> int:
        held: int = self.held["bytes"]
        return held

    def digest(self, which: str | None = None) -> str:
        held: str = self.held[which or DECIDES]
        return held

    @override
    def __repr__(self) -> str:
        return f"<Step {self.what}: {self.name}, {self.bytes} bytes>"


class Edition:
    """One rebuild: what it is, what it is read from, and what it becomes."""

    def __init__(
        self,
        name: str,
        summary: str,
        reads: str,
        writes: str,
        size: int,
        before: Mapping[str, Any],
        after: Mapping[str, Any],
        source: Mapping[str, Any],
        patch: Mapping[str, Any],
    ) -> None:
        self.name = name
        self.summary = summary
        self.reads = reads
        self.writes = writes
        self.size = size
        self.before = before
        self.after = after
        self.source = source
        self.patch = patch

    def chain(self) -> tuple[Step, ...]:
        """Every file between a cartridge somebody owns and what this writes.

        In the order it is walked, which is also the order somebody without any of
        it has to obtain things. Only the last step is one this repository makes.
        """
        return (
            Step("source", self.source["name"], self.source),
            Step("patch", self.patch["name"], self.patch),
            Step("reads", self.reads, dict(self.before, bytes=self.size)),
            Step("writes", self.writes, dict(self.after, bytes=self.size), produced=True),
        )

    @override
    def __repr__(self) -> str:
        return f"<Edition {self.name}, {self.size} bytes>"


def load_patch(path: Path | str | None = None) -> Patch:
    """What the manifest says about the hack both images are built with."""
    with Path(path or MANIFEST).open() as handle:
        held = json.load(handle)["patch"]
    return Patch(
        name=held["name"],
        version=held["version"],
        author=held["author"],
        where=held["where"],
        note=held["note"],
        archive=held["archive"],
    )


def load(path: Path | str | None = None) -> tuple[Edition, ...]:
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
            source=entry["source"],
            patch=entry["patch"],
        )
        for entry in held["editions"]
    )


EDITIONS = load()

PATCH = load_patch()


def matching(digest: str, among: Sequence[Edition] | None = None) -> Edition | None:
    """The edition an image with that deciding digest is, or nothing."""
    for edition in EDITIONS if among is None else among:
        if edition.before[DECIDES] == digest:
            return edition
    return None


def named(name: str, among: Sequence[Edition] | None = None) -> Edition:
    """The edition of that name."""
    among = EDITIONS if among is None else among
    for edition in among:
        if edition.name == name:
            return edition
    raise UnknownEdition(
        f"{name} is not an edition this corrects;"
        f" there are {', '.join(edition.name for edition in among)}"
    )
