# Open questions

What this project does not know for certain, and what it would take to find out.

This is the shortest list in the family, and the reason is the subject. This
repository corrects twelve bytes in each of two images, and almost all of its
work is refusing to touch anything else. It models no part, decompresses nothing,
and claims nothing about timing: the members it calls make every claim there is.

What that leaves is one figure that comes from a rule rather than a printed row,
and two boundaries listed so nobody mistakes them for gaps.

Every entry is also in
[`conformance/divergences.json`](conformance/divergences.json) with its status
and severity, so a program can read what a person reads here.

## Why the pinned digests cannot close anything

They are the strongest thing here and they answer one question: whether the file
in front of you is the file the manifest names. They cannot say the manifest is
right, and once already it was not.

That is worth being concrete about. What this correction writes changed on
2026-08-25, because the checksum it wrote was wrong for an image whose length is
not a power of two, and both of these are twelve megabytes. The member below this
one fixed the rule, and following the manual took agreement with real cartridges
from 2,150 of 2,780 retail images to 2,768. The digests this tool produced before
that are recorded under `supersedes` in
[`roms.manifest.json`](roms.manifest.json) with the upstream commit and the
reason, rather than deleted.

A digest updated to make a check pass would have hidden exactly that.

## What would settle almost all of them

One more page of Nintendo's manual, for the single entry below that is a question
at all.

## Where a figure comes from a rule rather than a printed row

### The size byte for a ninety six megabit image.

**The document says.** Nintendo tabulates five sizes, the largest of which is 64
megabit. Ninety six is not among them.

Source: Nintendo, *SNES Development Manual, Book 1*, manual page 1-2-18, read on
2026-08-27 from a rendered page. The five rows pair a code with a range: `09H` is
`3 ~ 4M Bit`, `0AH` is `5 ~ 8M Bit`, `0BH` is `9 ~ 16M Bit`, `0CH` is `17 ~ 32M
Bit`, and `0DH` is `33 ~ 64M Bit`. This entry used to say the largest was 32
megabit, which was wrong by one row.

**What this project follows.** The rule the table implies, which is the exponent
of the smallest power of two that holds the image.

**Why.** A five row table cannot be the whole answer, because cartridges below
its smallest row exist and carry a size byte. The rule reproduces every row the
manual prints, and now that the codes have been read it reproduces both halves of
every row rather than only the ranges: the code is the exponent of the size in
kilobytes, so 4M gives `09H`, 8M gives `0AH`, 16M `0BH`, 32M `0CH` and 64M `0DH`,
which is all five. Ninety six megabit rounds to the next power of two and gives
`0EH`, in a row the manual does not print.

**What would settle or reopen it.** A passage in Book I or Book II tabulating
sizes past 64 megabit. Book I was searched on 2026-08-27 with the document on the
machine and its pages rendered; the table ends at `0DH` and nothing beside it
gives the rule as a formula.

## Where the question is a scope boundary, not an unknown

### That the input is somebody's hack.

**The family's rule.** A hack is never evidence about hardware.

**What this project does.** Takes an image somebody else decompressed and
corrects the header that decompression left inconsistent.

**Why it is not a violation.** The hack is not being used as evidence here. It is
the subject. Nothing about a retail cartridge is inferred from it, and nothing
about it is offered as a fact about silicon.

**What would settle or reopen it.** Nothing. This is a boundary rather than an
unknown, and it is written down because the rule it sits next to is one somebody
would otherwise think had been broken.

### Everything about hardware.

**What this project does.** Reads a file, rewrites thirty two bytes of it in
every mirror, and writes it back.

**Why.** It models no part and claims nothing about timing. Where a header sits
is `snes-mapper`, what a header means and how its checksum is calculated is
`snes-rom-image`, and both are members with their own records and their own open
questions.

**What would settle or reopen it.** Nothing. Adding a claim about hardware here
would be adding a second source of truth for something a member already answers.

## What is not in question

So the boundary is visible rather than implied:

- **What changes.** Twelve bytes per image: six per header mirror, and there are
  two mirrors. A test asserts that nothing outside a header mirror moves, so the
  claim is checked rather than stated.
- **That the correction is idempotent.** The conformance run performs it twice
  and compares what came out, because a correction that is not idempotent is one
  nobody can safely re-run, and both runs write a file of the right length.
- **Every link of both chains.** Four digests each, at every step between a
  cartridge somebody owns and the image this writes, so a report can name which
  step to redo rather than only saying the last one did not match.
- **That all four digests are confirmed, not just the deciding one.** Publishing
  a crc32 beside a sha256 and never looking at the crc32 is publishing
  decoration.
- **That a superseded output is told apart from a wrong one.** The manifest
  records the digests an older correction produced beside the reason they
  changed, so a reader holding one is told it is a revision old rather than told
  it is broken.

## What is deliberately not modelled

Absent rather than unknown, and absent on purpose:

- **The decompression.** neviksti's patch is what turns a six megabyte cartridge
  into a twelve megabyte image. This repository does not perform it, does not
  carry it, and does not link to it. It corrects what it produced.
- **Any image.** Neither is here and neither is reconstructible from anything in
  this repository. Everything published is a digest.
- **Anything with a clock.** These are files.
