"""Correct the header of two Star Ocean rebuilds that no longer carry a chip.

Star Ocean shipped on an S-DD1 board. neviksti's Star Ocean no S-DD1/96Mbit hack
decompresses the graphics ahead of time and rebuilds the cartridge at ninety six
megabit, so the chip is not needed. Both rebuilds still declare it, and both
declare eight megabytes while being twelve.

Twelve bytes per image fix that, six in each of two header mirrors. None of the
arithmetic lives here: `snes-rom-image` rewrites the mirrors and recomputes the
checksum, `snes-mapper` decides where a header sits, and both are submodules.
What is here is the checking either side of that, and the table of what every
file in the chain should be.

Two entry points, and the difference between them is whether anything is written.

    from starocean import look, report      # reads only, says what is here
    from starocean import apply, run        # confirm, correct, confirm, write
"""

from .editions import (
    DECIDES,
    DIGEST_WIDTHS,
    DIGESTS,
    EDITIONS,
    EXPECTED_BYTES,
    PATCH,
    Edition,
    Patch,
    Step,
    UnknownEdition,
    load,
    load_patch,
    matching,
    named,
)
from .fix import (
    Corrupt,
    Missing,
    NotACartridge,
    Unexpected,
    Unrecognised,
    apply,
    confirm,
    correct,
    digests_of,
    run,
    source_directory,
)
from .verify import (
    ABSENT,
    ALTERED,
    CORRUPT,
    MATCHES,
    NOTHING,
    SOUND,
    WRONG,
    Finding,
    look,
    report,
    verdict,
)
from .version import VERSION

__version__ = VERSION

__all__ = [
    "ABSENT",
    "ALTERED",
    "CORRUPT",
    "DECIDES",
    "DIGESTS",
    "DIGEST_WIDTHS",
    "EDITIONS",
    "EXPECTED_BYTES",
    "MATCHES",
    "NOTHING",
    "PATCH",
    "SOUND",
    "VERSION",
    "WRONG",
    "Corrupt",
    "Edition",
    "Finding",
    "Missing",
    "NotACartridge",
    "Patch",
    "Step",
    "Unexpected",
    "UnknownEdition",
    "Unrecognised",
    "apply",
    "confirm",
    "correct",
    "digests_of",
    "load",
    "load_patch",
    "look",
    "matching",
    "named",
    "report",
    "run",
    "source_directory",
    "verdict",
]
