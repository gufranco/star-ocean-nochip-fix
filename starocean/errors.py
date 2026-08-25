"""Everything this package raises, in one place.

One module so a caller can see the whole set at once, and so `except` has
somewhere to import from. It imports nothing from the rest of the package, which
is what keeps it from ever closing a cycle: everything here raises, so everything
here imports this, and an import running the other way would make the order
modules happen to load in decide whether the package works at all.

It imports nothing from `romimage` either, which this package consumes as a
submodule, nor from `mapper` one level below that. A refusal this package makes
is this package's, and inheriting one from a member it depends on would make a
caller's `except` depend on which of the three raised.

Five of the six are the same question asked of a file a reader supplied: was this
the file the manifest names, and if not, in what way. They are separate classes
because the answers have separate fixes, and a caller telling them apart is most
of what this package is for. A single refusal saying the digest did not match
would tell a reader nothing they could act on.
"""

from __future__ import annotations


class NotACartridge(Exception):
    """The path is not a file this package can read at all.

    Raised before anything is hashed, because a directory, a symlink to nothing
    or a device node is not a wrong cartridge. It is not a cartridge.
    """


class Unrecognised(Exception):
    """The file was read and matches nothing in the manifest.

    The furthest-from-actionable of the refusals, and the one whose message works
    hardest: it prints the digest that was computed so a reader can search for it,
    rather than only saying that it did not match.
    """


class Corrupt(Exception):
    """The file matches a dump the manifest records as bad.

    Distinct from `Unrecognised` because the answer is different. This one says
    the reader has a known-broken copy rather than an unknown one, which turns a
    search into a re-download.
    """


class Unexpected(Exception):
    """The file is a cartridge the manifest knows and not the one asked for.

    A reader who supplied the other edition, or the same edition at a different
    revision, gets told which one they supplied. Refusing without naming it would
    send them looking for a fault in a file that is perfectly good.
    """


class Missing(Exception):
    """Nothing was supplied where something had to be.

    Separate from `NotACartridge` because an absent file and an unreadable one
    are different mistakes: one is a step not taken, the other a step taken
    wrongly.
    """


class UnknownEdition(Exception):
    """No edition goes by that name.

    The message names the editions that would have worked, because a refusal that
    does not costs the caller a search through the source. There are two.
    """
