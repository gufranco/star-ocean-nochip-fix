# Working in this repository

This file is for a coding agent. A person reading it will not be harmed, but
[README.md](README.md) is the document written for them.

## What this project is, in one paragraph

An image of Star Ocean that somebody else has already decompressed carries a
header describing a cartridge that no longer exists: it declares a coprocessor
that was removed and a size that is no longer its own. This corrects that header
in every mirror and recomputes the checksum. It decompresses nothing, models no
part, and knows nothing about time.

## The interface a caller drives

Two commands and a small library. `look` reads, `apply` corrects a supplied image
and hands back the bytes, and neither writes anything. `run` is the one that
writes.

- `look(where, editions, into)` reads every link of every chain and reports each
  as absent, matching, altered or corrupt. `report` turns those into lines and
  `verdict` into one word: `sound`, `wrong` or `nothing`. The last two are
  different answers on purpose, because a run that found nothing to check is not
  a run that found something broken.
- `apply(image, edition)` corrects a supplied image in memory.
- `confirm(data, edition)` is the check both ends of the run make.
- `named(name)` and `matching(digests)` reach an edition by its name or by what a
  file turned out to be.

Everything the package raises lives in
[`starocean/errors.py`](starocean/errors.py) and nowhere else, and that module
imports nothing from this package, nor from the member it consumes. There are
six, and they are separate classes because their fixes are separate: a file that
is not a file, one that matches nothing, one that matches a known bad dump, one
that is a cartridge but the wrong one, one that is absent, and a name no edition
goes by. A single refusal saying the digest did not match would tell a reader
nothing they could act on.

There is no clock and no part. These are files.

## The authority ladder

This one pins almost nothing, and that is the point.

1. **`snes-rom-image-python`**, which pins what a header means against Nintendo's
   development manual and does the rewrite.
2. **`snes-mapper-python`**, which pins where a header sits.
3. **The image itself**, confirmed by four digests before anything touches it and
   four more before the result is written.

`conformance/hardware.json` holds two facts and no more: the image length and the
size byte that follows from it. Everything else a reader might expect to find
here is in a sibling, on purpose. **A fact in two files is a fact that will
drift**, and the sibling is the one pinned against the manual.

## What is settled and what is not

**Settled: what changes.** Twelve bytes per image, six per header mirror across
two mirrors, and a test asserts that nothing outside a mirror moves.

**Settled: that the correction is idempotent.** The conformance run performs it
twice and compares what came out.

**Settled: every link of both chains.** Four digests each, at every step between
a cartridge somebody owns and the image this writes.

**Not settled: 3 things**, each in [OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) with
what would close it. One is a size byte that comes from a rule rather than a
printed row, and two are boundaries listed so nobody mistakes them for gaps.

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

## A pinned digest was wrong once, and the record says so

What this correction writes changed on 2026-08-25. The checksum it wrote was
wrong for an image whose length is not a power of two, and both of these are
twelve megabytes. The member below this one fixed the rule, and following the
manual took agreement with real cartridges from 2,150 of 2,780 retail images to
2,768.

The digests this tool produced before that are in
[`roms.manifest.json`](roms.manifest.json) under `supersedes`, with the upstream
commit and the reason, rather than deleted. That is what lets a reader holding an
older output be told it is one revision old instead of being told it is broken.

**A digest updated to make a check pass would have hidden exactly that.** When a
submodule bump changes what this writes, find the upstream commit that changed it
and why before touching anything that records what the output should be.

## Every gate, in the order to run them

```bash
ruff format --check .
ruff check .
mypy
pnpm run format:check
python3 -m coverage erase
for file in $(find starocean conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
```

Then the throughput floor, which runs outside the coverage step because a tracer
costs about ten times what the digests do:

```bash
python3 -m conformance.speed
```

And, with an image present, the run against the real files:

```bash
python3 -m conformance.against_images
```

`conformance/hardware.test.py` is in the coverage loop and needs no image. The
tests that need one skip rather than pass when it is absent, so a run that proved
nothing never reads as a run that proved something.

Everything under `conformance/` runs as a module. Run as a script, its own
directory goes on the import path and a file there shadows any standard library
module of the same name.

## Conventions that are not negotiable

| Thing | Rule |
|:------|:-----|
| Language | Python only |
| Comments | None in source. Docstrings carry the reasoning, and say why rather than what |
| Test layout | `<module>.test.py` beside the module it covers |
| Test structure | Arrange, blank line, one act, blank line, assert. No section labels |
| Package manager for tooling | pnpm, never npm |
| Commits | Conventional Commits |
| Coverage | 100% statements and branches, enforced |
| Types | `mypy` at strict, plus every optional error class |
| Images | Never committed, in any form, for any reason. A digest is published; a byte of content is not |
| Header knowledge | Belongs in the siblings. Adding a copy here creates a second source of truth |
| The dependency | A submodule pinned by commit, never a copied file. See [FAMILY.md](FAMILY.md) |
## Layout

```
starocean/
  editions.py    the two chains, their digests, and looking one up
  fix.py         confirming, correcting, confirming again, writing
  verify.py      reading only, and what each link turned out to be
  errors.py      everything this package raises, importing nothing from it or from romimage
  version.py     rewritten by the release job and by nothing else
conformance/
  against_images.test.py  the real files, when they are here
  hardware.json           the two facts this file pins, and no more
  divergences.json        where a figure comes from a rule rather than a printed row
  links.py                the weekly check that every cited address still answers
  speed.py                the throughput floor
roms.manifest.json        every filename and four digests per link, and the superseded ones
snes-rom-image-python/    the header reader, a submodule, with the memory map nested below it
```

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

## Before calling anything finished

[`FAMILY.md`](FAMILY.md) carries a checklist under "What a new repository has to
have before it is a member". Every line on it was a defect found in one of these
repositories and fixed in all of them, so it is the list of things that have
actually gone wrong here rather than a list of good intentions. Read it before
adding a surface, and read it again before saying a change is done.

A change to `FAMILY.md` is a change to every member. Nothing here can catch it
being made in one of them and forgotten in the others, because a test in this
repository cannot see the others, so the check is a command rather than a suite:

```sh
shared() { sed '/^\*Everything above this line/q' "$1"; }

grep -o 'github\.com/[^/]*/\([a-z0-9-]*\))' FAMILY.md | sed 's|.*/||; s|)||' | sort -u |
while read -r member; do
  other="../$member/FAMILY.md"
  [ -f "$other" ] || { echo "not on this machine: $member"; continue; }
  cmp <(shared FAMILY.md) <(shared "$other") && echo "match: $member"
done
```

The members come from the table at the top of `FAMILY.md` rather than from a glob
over the parent directory. The submodule under this repository carries a copy of
that file too, and it is a member in its own right rather than a copy to compare
against from here.

Two rules from that file are worth repeating because they are the ones skipped
most often:

**A check nobody has seen fail is not known to work.** Drive it, once,
deliberately, against input that should fail it.

**Silence and success produce the same output.** A run that found no image
reports `nothing` rather than `sound`, which is the whole reason those are two
words.

## What a change is expected to leave behind

A gate that would have caught the bug. A change that alters what this writes also
updates the manifest, records the digests it replaces under `supersedes` with the
upstream commit and the reason, and never the other way round.
