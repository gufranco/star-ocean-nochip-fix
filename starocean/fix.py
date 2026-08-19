"""Read an image, confirm it is the one named, correct it, confirm the result.

The correction is small and someone else's packages do all of it: `snes-mapper`
decides where the header sits and `snes-rom-image` rewrites every mirror of it and
recomputes the checksum. What is left here is the part that makes the small change
safe to run unattended, which is checking at both ends.

The order matters and is the whole design. An image is confirmed against four
digests before anything touches it, so a file that is not the one named never
reaches the rewrite. The result is confirmed against four more before it is
written, so a rewrite that produced something unforeseen ends as a refusal rather
than as a file on disk that looks finished.

Neither check is a formality. A header rewrite that goes wrong produces a file of
exactly the right length that boots into nothing, and the only cheap way to tell
that apart from a correct one is to have written down beforehand what correct is.
"""

import hashlib
import os
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "snes-rom-image"))
sys.path.insert(0, str(ROOT / "packages" / "snes-rom-image" / "packages" / "snes-mapper"))

from romimage import rewrite
from romimage.rewrite import NoHeader

from starocean import editions

DIRECTORY_VARIABLE = "STAR_OCEAN_ROM_DIR"

DEFAULT_SOURCE = ROOT / "roms"

DEFAULT_DESTINATION = ROOT / "dist"


class NotACartridge(Exception):
    pass


class Unrecognised(Exception):
    pass


class Corrupt(Exception):
    pass


class Unexpected(Exception):
    pass


class Missing(Exception):
    pass


def source_directory(environment=None):
    """Where the images are read from: what was named, or the folder in here.

    A named directory wins even when it turns out to be empty. Quietly falling back
    from a path somebody typed turns their typo into a run that skips everything
    and reports that nothing needed doing.
    """
    named = (environment if environment is not None else os.environ).get(DIRECTORY_VARIABLE)
    return Path(named) if named else DEFAULT_SOURCE


def digests_of(image):
    """Every digest the manifest pins, for one image."""
    return {
        "crc32": f"{zlib.crc32(image) & 0xFFFFFFFF:08x}",
        "md5": hashlib.md5(image).hexdigest(),
        "sha1": hashlib.sha1(image).hexdigest(),
        "sha256": hashlib.sha256(image).hexdigest(),
    }


def correct(image):
    """The same image declaring no coprocessor, its real size, and a live checksum."""
    try:
        return rewrite.declare_rom_only(image)
    except NoHeader as reason:
        raise NotACartridge(
            f"nothing in these {len(image)} bytes reads as a cartridge header,"
            " so there is no header to correct"
        ) from reason


def confirm(image, edition):
    """That this really is the image the edition names, before anything is changed."""
    if len(image) != edition.size:
        raise Unrecognised(
            f"{edition.name} is {edition.size} bytes and this is {len(image)}."
            " A file of the wrong length is a different build rather than a"
            " different copy of this one"
        )

    found = digests_of(image)
    if found[editions.DECIDES] != edition.before[editions.DECIDES]:
        raise Unrecognised(
            f"this is the right length for {edition.name} but not the right content:"
            f" its {editions.DECIDES} is {found[editions.DECIDES]} and the manifest"
            f" pins {edition.before[editions.DECIDES]}. A file of the right length"
            " with the wrong content is usually a different revision of the rebuild"
        )

    _cross_check(edition.name, edition.before, found)
    return edition


def _cross_check(name, pinned, found):
    """The other three digests have to agree as well.

    Reaching here means the deciding digest already matched, so a disagreement is
    not a different file: it is a manifest contradicting itself, which is worth
    saying out loud rather than passing over.
    """
    for digest in editions.DIGESTS:
        if digest == editions.DECIDES or digest not in pinned:
            continue
        if pinned[digest].lower() != found[digest]:
            raise Corrupt(
                f"{name} matches on {editions.DECIDES} but not on {digest}:"
                f" the manifest says {pinned[digest]} and the file gives {found[digest]}."
                " A manifest that disagrees with itself was edited by hand or built"
                " from two different copies"
            )


def apply(image, edition):
    """Confirm, correct, confirm again, and hand back the bytes."""
    confirm(image, edition)
    produced = correct(image)
    found = digests_of(produced)

    if found[editions.DECIDES] != edition.after[editions.DECIDES]:
        raise Unexpected(
            f"correcting {edition.name} produced an image whose {editions.DECIDES} is"
            f" {found[editions.DECIDES]}, and the manifest pins"
            f" {edition.after[editions.DECIDES]}. The input was the one named, so"
            " something about the correction itself has changed"
        )

    _cross_check(f"{edition.name} after correction", edition.after, found)
    return produced


def run(edition, source, destination):
    """Correct one edition from a directory into a directory."""
    reading = Path(source) / edition.reads
    if not reading.is_file():
        raise Missing(
            f"{edition.reads} is not in {source}. A copy you already own goes there,"
            " or wherever the source directory points"
        )

    produced = apply(reading.read_bytes(), edition)
    Path(destination).mkdir(parents=True, exist_ok=True)
    writing = Path(destination) / edition.writes
    writing.write_bytes(produced)
    return writing


def main(argv, catalogue=None):
    source = Path(argv[0]) if argv else source_directory()
    destination = Path(argv[1]) if len(argv) > 1 else DEFAULT_DESTINATION
    catalogue = editions.EDITIONS if catalogue is None else catalogue
    done = refused = 0

    for edition in catalogue:
        try:
            written = run(edition, source, destination)
        except Missing as reason:
            print(f"  {edition.name}: not here, {reason}")
            continue
        except (NotACartridge, Unrecognised, Corrupt, Unexpected) as reason:
            refused += 1
            print(f"  {edition.name}: refused, {reason}")
            continue
        done += 1
        print(f"  {edition.name}: {edition.reads}")
        print(f"    -> {written} ({edition.after[editions.DECIDES]})")

    if refused:
        print(f"  {refused} refused, nothing was written for them")
        return 1
    if not done:
        print(f"  neither image was found in {source}, so nothing was written")
        return 2
    print(f"  {done} of {len(catalogue)} corrected")
    return 0


def command():
    """The installed console command, which takes its arguments from the shell."""
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    command()
