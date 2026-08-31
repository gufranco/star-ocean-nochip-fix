"""Look at this machine and say what is actually here, so a report can be believed.

What goes wrong with this package is rarely a defect in it. It is a submodule
that was never checked out, or an image somebody supplied that is a link earlier
in the chain than the one this reads. Both look the same from outside: nothing
happens and it is not obvious why.

The submodule is the sharp one. What a header means is not this package's claim;
it is `snes-rom-image-python`, carried here as a submodule and imported by name.
A checkout without `--recurse-submodules` leaves the directory there and empty,
and what fails is an import rather than a check, which reads as a broken package
rather than an incomplete checkout.

Where this stops and `verify` begins is worth stating. `verify` answers whether
the files a reader holds are the files the manifest names, one line per link of
the chain. This answers whether the machine can do anything at all, and then
says how many of those files are here. A reader with no images gets a complete
report from this and an empty one from `verify`.

Two rules shape it, and they are the whole point.

Nothing is hidden. A check that fails says what it saw, and a check that itself
throws is caught and reported as what it threw, named by its type. An absent
library is reported as absent rather than as a failure, because a fresh checkout
has none and that is the normal state, but it is never reported as nothing at all.

Nothing is imported from the package at the top of this file, and that is
deliberate rather than tidy. This package imports `snes-rom-image-python` by name,
so on the machine this exists to diagnose, a checkout with no submodule,
importing it here would fail before a single finding was printed. The reader
would get a traceback naming a module they have never heard of instead of a line
telling them to fetch the submodule.

Which is also why this is run as a file rather than with `-m`. Either form has to
read the package's `__init__` first, and that is the import that fails. Run it as

    python3 starocean/doctor.py

and everything that can fail happens inside a finding, where its failure is the
report rather than the end of it.

Nothing is inferred. Every line is something looked at on this machine just now,
including every file of every chain, looked for on disk rather than assumed from
what a manifest says should be there.
"""

from __future__ import annotations

import json
import platform
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable, Sequence


def _version(where: Path | None = None) -> str:
    """The package version, read out of the file beside this one.

    Read rather than imported. Importing it would go through the package, and
    the package is what fails on the machine this exists to diagnose.
    """
    found = re.search(
        r"""VERSION\s*[:=][^"']*["']([^"']+)["']""",
        (where or Path(__file__).resolve().parent / "version.py").read_text(),
    )
    return found.group(1) if found else "unknown"


VERSION = _version()

ROOT = Path(__file__).resolve().parent.parent

from starocean import environment  # noqa: E402

MANIFEST = ROOT / "editions.manifest.json"

SOURCE = ROOT / "roms"

DESTINATION = ROOT / "dist"

WRITES = "writes"
"""The one step of a chain that is looked for where it is written, not where it is read."""

STEPS = 4
"""Source cartridge, patch, decompressed image, corrected image."""

SUBMODULES = ("snes-rom-image-python",)

OLDEST_PYTHON = (3, 12)


class Finding:
    """One thing that was looked at, and what was there."""

    __slots__ = ("advice", "detail", "name", "ok")

    def __init__(self, name: str, ok: bool, detail: str, advice: str | None = None) -> None:
        self.name = name
        self.ok = ok
        self.detail = detail
        self.advice = advice

    @property
    def line(self) -> str:
        """The one-line form, which is what a reader scans."""
        return f"  {'ok  ' if self.ok else '   !'}  {self.name}: {self.detail}"

    @property
    def report(self) -> str:
        """The same, with what to do about it when there is something to do."""
        if self.ok or not self.advice:
            return self.line
        return f"{self.line}\n         {self.advice}"

    @override
    def __repr__(self) -> str:
        return f"<Finding {self.name} {'ok' if self.ok else 'not ok'}>"


def _python() -> Finding:
    return Finding(
        "python",
        sys.version_info[:2] >= OLDEST_PYTHON,
        f"{platform.python_version()} on {platform.system()} {platform.machine()}",
        f"this package needs {OLDEST_PYTHON[0]}.{OLDEST_PYTHON[1]} or newer",
    )


def _package() -> Finding:
    return Finding("starocean", True, f"version {VERSION}")


def _loaded() -> Any:
    """The package, imported now rather than when this file was read.

    Imported by name rather than relatively, and with the repository put on the
    path first, because this file is run as a script and a relative import has
    no package to be relative to. A single place for it, so every finding fails
    the same way when the submodule is absent and the failure is a line in the
    report rather than a traceback in place of one.
    """
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from starocean import editions, verify

    return editions, verify


def _editions() -> Finding:
    """Which editions this correction knows, and that each one names a full chain."""
    try:
        editions, _ = _loaded()
        held = editions.EDITIONS
    except Exception as trouble:
        return Finding(
            "editions",
            False,
            f"{type(trouble).__name__}: {trouble}",
            "the package could not be imported, so nothing below it could be"
            " looked at; the submodule line says why",
        )
    short = sorted(one.name for one in held if len(one.chain()) < STEPS)
    return Finding(
        "editions",
        not short,
        ", ".join(f"{one.name} at {one.size} bytes" for one in held),
        f"{', '.join(short)} names fewer than {STEPS} steps, and a chain with a"
        " link missing cannot say which step to redo",
    )


def _chain() -> list[Finding]:
    """Every link of every chain, and whether the file is on this machine.

    One line per link rather than one per edition, because the answer a reader
    needs is which step to redo. An edition reported only as absent sends them
    back to the beginning of a four step chain.
    """
    try:
        editions, _ = _loaded()
        held = editions.EDITIONS
    except Exception:
        return []
    found = []
    for one in held:
        for step in one.chain():
            place = DESTINATION if step.what == WRITES else SOURCE
            where = place / step.name
            found.append(
                Finding(
                    f"{one.name}: {step.what}",
                    True,
                    f"{step.name} is at {place.name}/"
                    if where.is_file()
                    else f"{step.name} is not at {place.name}/",
                )
            )
    return found


def _submodule(name: str, root: Path = ROOT) -> Finding:
    """Whether a submodule is checked out, since its absence is silent otherwise.

    The marker is the manifest rather than the directory. Git creates the empty
    directory for a submodule it has not fetched, so a check on the path alone
    reports a present submodule on exactly the machine where it is missing.
    """
    where = root / name
    if (where / "pyproject.toml").is_file():
        return Finding(f"submodule {name}", True, f"checked out at {where}")
    return Finding(
        f"submodule {name}",
        False,
        f"{where} is empty" if where.is_dir() else f"{where} is not there",
        "this package imports it by name, so nothing here runs without it;"
        " git submodule update --init --recursive",
    )


def _manifest(path: Path | str = MANIFEST) -> Finding:
    """What the manifest pins, or why it could not be read."""
    try:
        held = json.loads(Path(path).read_text())
    except OSError as trouble:
        return Finding(
            "manifest",
            False,
            f"could not be read: {trouble}",
            "the manifest is what every digest is checked against; without it"
            " nothing can be identified at all",
        )
    except ValueError as trouble:
        return Finding(
            "manifest",
            False,
            f"is not readable as JSON: {trouble}",
            "the file is here and damaged, which is worse than absent",
        )
    named = held.get("editions") or []
    superseded = [one for one in named if one.get("supersedes")]
    return Finding(
        "manifest",
        bool(named),
        f"{len(named)} editions pinned"
        + (
            f", {len(superseded)} carrying superseded digests"
            if superseded
            else ", none carrying superseded digests"
        ),
        "a manifest pinning nothing identifies nothing",
    )


def _source(where: Path = SOURCE) -> Finding:
    """Where images are looked for, and whether anything is there."""
    if not where.is_dir():
        return Finding(
            "images",
            True,
            f"no {where}, so there is nothing to correct on this machine yet",
        )
    try:
        present = [one for one in where.iterdir() if one.is_file()]
    except OSError as trouble:
        return Finding("images", False, f"could not be read: {trouble}")
    return Finding(
        "images",
        True,
        f"{len(present)} files at {where}"
        if present
        else f"{where} is here and empty, so there is nothing to correct yet",
    )


def examine(
    manifest: Path | str = MANIFEST,
    root: Path = ROOT,
    source: Path = SOURCE,
) -> list[Finding]:
    """Everything worth looking at on this machine, in the order a reader wants it."""
    return [
        _python(),
        _package(),
        _editions(),
        *(_submodule(name, root) for name in SUBMODULES),
        _manifest(manifest),
        _source(source),
        *_chain(),
    ]


def report(found: Sequence[Finding]) -> list[str]:
    """The lines a person pastes into an issue."""
    unwell = [one for one in found if not one.ok]
    lines = [f"starocean {VERSION} on {platform.python_version()}, {platform.system()}", ""]
    lines.append("  the machine")
    lines.extend(environment.lines(ROOT))
    lines.append("")
    lines.append("  this package")
    lines.extend(one.report for one in found)
    lines.append("")
    if unwell:
        lines.append(f"  {len(unwell)} of {len(found)} checks did not pass")
    else:
        lines.append(f"  {len(found)} checks, nothing to report")
    return lines


def main(
    argv: Sequence[str] = (),
    examine: Callable[..., list[Finding]] = examine,
    say: Callable[[str], None] = print,
) -> int:
    found = examine()
    for line in report(found):
        say(line)
    return 1 if any(not one.ok for one in found) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
