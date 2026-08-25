# ROMs

Nothing in this directory is shared. The game belongs to its publisher, the
S-DD1 removal is neviksti's work and the English translation is DeJap's. No part
of any of it is carried by this repository, published in the manifest, or
reconstructible from anything here. What the manifest holds is a name, a length
and four digests, and a digest reconstructs nothing.

Put copies you already own here and the correction runs. Leave the directory
empty and the checks that need one report as skipped rather than as passed, so a
run that proved nothing never reads as a run that proved something.

## The chain

Star Ocean no S-DD1/96Mbit hack version 1.0, by neviksti.
Where it lives: https://www.romhacking.net/hacks/614/

Two patches, not interchangeable. For the English chain the DeJap translation is applied first and this patch second; the other order does not work. Neither patch is carried here.

Four files per edition, and every one of them is pinned. `star-ocean-verify`
looks for all four and says which link is wrong, which is more useful than being
told the image is not the one named when the real problem happened two steps
earlier.

## Where they go

Here, keeping the filenames below, or anywhere `STAR_OCEAN_ROM_DIR` points.
Subdirectories are walked. A named directory wins even when it turns out to be
empty, because quietly falling back from a path somebody typed turns a typo into
a run that reports nothing needed doing.

## The patch archive

| Field | Value |
|-------|-------|
| File | `Star Ocean 96Mbit patch - xdelta.zip` |
| Bytes | 5514721 |
| crc32 | `0c533f68` |
| md5 | `00feb1f170127af9b12f5c6c825b695d` |
| sha1 | `ba3681fad685a278ffe5858b4f8e5cbfe4fb016f` |
| sha256 | `f820128d161f5e3fea8a839100b08c63fd435f433e28269ff95e63907a18b2c0` |

## What this writes changed on 2026-08-25

The digests below for the corrected images are not the ones this tool produced
before that date. The checksum it writes was wrong for an image whose length is
not a power of two, and both of these are twelve megabytes.

`snes-rom-image-python` fixed the rule: the development manual says the
remainder is added repeatedly until the total reaches a power of two, and a
remainder that is not itself a power of two folds the same way first. Following
it took agreement with real cartridges from 2,150 of 2,780 retail images to
2,768. Both corrected images now carry a checksum that matches what the rule
computes over them, and a complement that sums with it to FFFF.

If you hold an image matching the previous digests, it carries a checksum no
cartridge would. Run the correction again. The manifest records the superseded
digests beside the reason, so a file that matches them can still be recognised
rather than merely failing to match.

## Per edition

### japanese

neviksti's patch on the Japanese original, decompressed to ninety six megabit.

**1. The cartridge it starts from.** The Japanese retail cartridge.

| Field | Value |
|-------|-------|
| File | `Star Ocean (Japan).sfc` |
| Bytes | 6291456 |
| crc32 | `3dbdfdbf` |
| md5 | `d686ba6df942084216393ada009126dc` |
| sha1 | `a616ee3466256482bc0adc11f1fda7c30e66ef8d` |
| sha256 | `efae37be832d0ea1490784d57bef00761a8bf0b5bcef9c23f558e063441c3876` |

**2. The patch applied to it.**

| Field | Value |
|-------|-------|
| File | `96Mbit_SO_JPN.xdelta` |
| Bytes | 3227030 |
| crc32 | `b0bff91f` |
| md5 | `d3a781639a0d4a5f05c8602be2c449f0` |
| sha1 | `6996194ef50db0a3aa214582bc56b6df33562912` |
| sha256 | `8c3869301f396f4403b51493cceda4c3b2d8da2e4eba8e91e2c58618e0f77099` |

**3. What that produces, and what this reads.**

| Field | Value |
|-------|-------|
| File | `Star Ocean (J) SDD1 Patched (Hack) v1 Neviksti.sfc` |
| Bytes | 12582912 |
| crc32 | `4dbe75be` |
| md5 | `2bfd0e8ed3510109d728a1bbf380827b` |
| sha1 | `947e4d19004f036d7586718d3414d36b64ecdf68` |
| sha256 | `e5ba9bef71c8ea31ce9650b90a60245c3434ff679475f847903011bf69e6d338` |

**4. What this writes.**

| Field | Value |
|-------|-------|
| File | `star-ocean-jp-nochip.sfc` |
| Bytes | 12582912 |
| crc32 | `e2f62c1e` |
| md5 | `075d99d327b4038f22263049fb160c64` |
| sha1 | `857453805be297f1d0f75b5e8a0af603bc507cbb` |
| sha256 | `4656c58a296b8901f29456e2920ab85778f84f923c52fda94fa77387695f2516` |

### english

The same patch on the DeJap English translation. The two are not interchangeable.

**1. The cartridge it starts from.** The Japanese retail cartridge with DeJap's English translation already applied.

| Field | Value |
|-------|-------|
| File | `Star Ocean (J) T+Eng v1.0 DeJap.sfc` |
| Bytes | 6291456 |
| crc32 | `6ba9e08d` |
| md5 | `217a97e694fb916ad26c8a471f6c0e84` |
| sha1 | `8574f0c49b0e823f21763331c2d66225b95c1653` |
| sha256 | `504050fcbcf1b6768448aed48298ad388b76271412a8cb9659937cddbe8e1385` |

**2. The patch applied to it.**

| Field | Value |
|-------|-------|
| File | `96Mbit_SO_ENG.xdelta` |
| Bytes | 2869793 |
| crc32 | `3cfe8cd5` |
| md5 | `dd9136abfbe02bf430960d67eb3d2e56` |
| sha1 | `95ec51cb2aba2f59d064241fd3041348e7f21050` |
| sha256 | `83b209ef73241fa37f6d355da3786ea2617b97a171ae98d535ec5ecaeb65d66e` |

**3. What that produces, and what this reads.**

| Field | Value |
|-------|-------|
| File | `Star Ocean (J) T+Eng, SDD1 Patched v1 DeJap, SDD1 v1 Neviksti.sfc` |
| Bytes | 12582912 |
| crc32 | `b1d82240` |
| md5 | `8ac766702be51975faab7a431c89d9b2` |
| sha1 | `7dbaa0265bb5d33422808bad1041cdc8f9585eb4` |
| sha256 | `1bcb3b8b58f19a91540aeb5ca975fe2386ca0b55a5ff924be6a3514010b2e5c3` |

**4. What this writes.**

| Field | Value |
|-------|-------|
| File | `star-ocean-en-nochip.sfc` |
| Bytes | 12582912 |
| crc32 | `4f487385` |
| md5 | `94103789fb45494fe8df9591e11c17d0` |
| sha1 | `d9f47ca39553f28c8e1ffac0924898616459e090` |
| sha256 | `3f0af092ae356444b1348526916d90ac5cd53af9a47c2e6b1d66e1dec3045a89` |

## What is checked

`sha256` decides at every link. The other three are confirmed too rather than
published and ignored: a file can be the right length under the right name and
still be a bad copy, and a manifest that publishes a crc32 and never looks at it
is publishing decoration. A file that matches the deciding digest but not the
rest is reported as corrupt rather than as wrong, because that is a defect in
this manifest rather than in anybody's copy.

The input is confirmed before anything touches it, so a file that is not the one
named never reaches the rewrite. The result is confirmed before it is written, so
a rewrite that produced something unforeseen ends as a refusal rather than as a
file on disk that looks finished.

## The law this rests on

A length and a digest are measurements of a file rather than expression, and
measurements sit outside what copyright reaches under 17 U.S.C. 102(b) and Feist
Publications v. Rural Telephone Service. Correcting a header on a copy you own is
the kind of examination and adaptation Sega v. Accolade and Sony v. Connectix hold
to be fair. None of that extends to the game, the translation or the patch, which
is why none of them is here.

