# Working in this repository

This file is for a coding agent. A person reading it will not be harmed, but
[README.md](README.md) is the document written for them.

## What this project is, in one paragraph

An image of Star Ocean that somebody else has already decompressed carries a
header describing a cartridge that no longer exists: it declares a coprocessor
that was removed and a size that is no longer its own. This corrects that header
in every mirror and recomputes the checksum. It decompresses nothing, models no
part, and knows nothing about time.

## The authority ladder, and why this file pins almost nothing

1. **`snes-rom-image-python`**, which pins what a header means against Nintendo's
   development manual and does the rewrite.
2. **`snes-mapper-python`**, which pins where a header sits.
3. **The image itself**, confirmed by four digests before anything touches it and
   four more before the result is written.

`conformance/hardware.json` holds two facts and no more: the image length and the
size byte that follows from it. Everything else a reader might expect to find
here is in a sibling, on purpose. **A fact in two files is a fact that will
drift**, and the sibling is the one pinned against the manual.

## The order matters, and it is the whole design

An image is confirmed against four digests *before* the rewrite, so a file that
is not the one named never reaches it. The result is confirmed against four more
*before* it is written, so a rewrite that produced something unforeseen ends as a
refusal rather than as a file on somebody's disk.

Weakening either end makes this unsafe to run unattended, which is the only
reason it exists in this shape.

## The input is a hack, and that is allowed here

The family's rule is that a hack is never evidence about hardware. It is not
being used as evidence: it is the subject. This takes an image somebody else
decompressed and corrects what that decompression left inconsistent. Nothing
about the patch is treated as telling anybody what a cartridge does.

## Every gate, in the order to run them

```bash
ruff format --check .                     # formatting
ruff check .                              # lint, zero warnings
mypy                                      # types, strict
pnpm run format:check                     # every JSON file
for f in starocean/*.test.py conformance/*.test.py; do python3 "$f"; done
python3 -m coverage report                # fails below 100%
```

`conformance/hardware.test.py` is in that loop and needs no image. The tests that
need one skip rather than pass when it is absent, so a run that proved nothing
never reads as a run that proved something.

## Things that will bite you

**The size byte comes from a rule, not a row.** Nintendo tabulates five sizes and
the largest is 32 megabit. Ninety six is not among them, so 0x0E comes from the
manual's rule that the byte is the base two logarithm of the length in kilobytes.
A reader checking the table will not find this value in it, which is why it is
named in `conformance/divergences.json`.

**Every mirror, not the first.** The rewrite belongs to the sibling and it changes
all of them. An image with one corrected header works in the tool it was tested
in and not on the machine it was built for.

**No image is in this repository**, only a manifest of names, lengths and four
digests each.

## Conventions

| Thing | Rule |
|:------|:-----|
| Language | Python only |
| Comments | None in source. Docstrings carry the reasoning, and say why rather than what |
| Test layout | `<module>.test.py` beside the module it covers |
| Test structure | Arrange, blank line, one act, blank line, assert. No section labels |
| Package manager for tooling | pnpm, never npm |
| Commits | Conventional Commits |
| Header knowledge | Belongs in the siblings. Adding a copy here creates a second source of truth |
