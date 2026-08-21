## What this changes

One or two sentences. What is different afterwards, and why it needed to be.

## How it was checked

Paste the output rather than describing it. A claim that the tests pass is not
evidence that they did.

```text
```

- [ ] `ruff format --check .` and `ruff check .` are clean
- [ ] `mypy` reports nothing
- [ ] Every test file runs, and coverage is 100% of statements and branches
- [ ] `conformance/hardware.test.py` still holds both constants to their record

## If this changes an edition, or adds one

Paste the run against an image you own, and give the digests at both ends. Never
attach the file.

The correction is confirmed at both ends on purpose: an image is checked against
four digests before anything touches it, and the result against four more before
it is written. A change that weakens either end makes this unsafe to run
unattended, which is the whole point of it.

## If this changes what a header means

It probably belongs in a sibling. What a header means is pinned in
`snes-rom-image-python` against Nintendo's manual, and where it sits is pinned in
`snes-mapper-python`. Adding a second copy here creates a source of truth that
will drift away from the first.

## What it does not carry

- [ ] No cartridge, no patch output, and no fragment of either
- [ ] Nothing that says where to obtain them
