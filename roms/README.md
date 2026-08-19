# ROMs

Nothing in this directory is shared. Both images are somebody else's work sitting
on top of somebody else's game, and no part of either is carried by this
repository, published in the manifest, or reconstructible from anything here. What
the manifest holds is a name, a length and four digests, and a digest reconstructs
nothing.

Put a copy you already own here and the correction runs. Leave the directory empty
and the checks that need one report as skipped rather than as passed, so a run that
proved nothing never reads as a run that proved something.

## Where they go

Here, keeping the filename below, or anywhere `STAR_OCEAN_ROM_DIR` points. A named
directory wins even when it turns out to be empty, because quietly falling back
from a path somebody typed turns a typo into a run that reports nothing needed
doing.

## What is corrected

Star Ocean shipped on an S-DD1 board, which decompressed graphics on the way to the
console. Somebody else decompressed all of it ahead of time and rebuilt the
cartridge at ninety six megabit, so the chip is no longer doing anything. Both
rebuilds still declare an S-DD1 in the header, and both declare eight megabytes
while being twelve.

Six bytes per header mirror: the chipset field, the size field, and the checksum
with its complement. Both mirrors, then the checksum recomputed over the result.

## The images that go in

### japanese

The Japanese rebuild, decompressed to ninety six megabit.

| Field | Value |
|-------|-------|
| File | `Star Ocean (J) SDD1 Patched (Hack) v1 Neviksti.sfc` |
| Bytes | 12582912 |
| crc32 | `4dbe75be` |
| md5 | `2bfd0e8ed3510109d728a1bbf380827b` |
| sha1 | `947e4d19004f036d7586718d3414d36b64ecdf68` |
| sha256 | `e5ba9bef71c8ea31ce9650b90a60245c3434ff679475f847903011bf69e6d338` |

### english

The same rebuild carrying the English translation.

| Field | Value |
|-------|-------|
| File | `Star Ocean (J) T+Eng, SDD1 Patched v1 DeJap, SDD1 v1 Neviksti.sfc` |
| Bytes | 12582912 |
| crc32 | `b1d82240` |
| md5 | `8ac766702be51975faab7a431c89d9b2` |
| sha1 | `7dbaa0265bb5d33422808bad1041cdc8f9585eb4` |
| sha256 | `1bcb3b8b58f19a91540aeb5ca975fe2386ca0b55a5ff924be6a3514010b2e5c3` |

## The images that come out

### japanese

| Field | Value |
|-------|-------|
| File | `star-ocean-jp-nochip.sfc` |
| Bytes | 12582912 |
| crc32 | `4cde067c` |
| md5 | `f4cf8181ecfcf553be8f6fcbac3d47cc` |
| sha1 | `1227eeb4339fc191c08caab33b9746df36425b85` |
| sha256 | `37131fc112149dc7946c229ade1e226aebc4e2749edf7cf9470bff6952760924` |

### english

| Field | Value |
|-------|-------|
| File | `star-ocean-en-nochip.sfc` |
| Bytes | 12582912 |
| crc32 | `6db1c7d3` |
| md5 | `40336902d0b865eecf0ffe1235c11333` |
| sha1 | `77107cba44e45928cf2fa1ed67390ed1f86649e0` |
| sha256 | `32bab94ed1abc94a3b0bc0e1315c88a759da82b995e4ab0f0d2970afe94a4ee5` |

## What is checked

`sha256` decides at both ends. The other three are confirmed too rather than
published and ignored: a file can be the right length under the right name and
still be a bad copy, and a manifest that publishes a crc32 and never looks at it is
publishing decoration.

The input is confirmed before anything touches it, so a file that is not the one
named never reaches the rewrite. The result is confirmed before it is written, so a
rewrite that produced something unforeseen ends as a refusal rather than as a file
on disk that looks finished.

## The law this rests on

A length and a digest are measurements of a file rather than expression, and
measurements sit outside what copyright reaches under 17 U.S.C. 102(b) and Feist
Publications v. Rural Telephone Service. Correcting a header on a copy you own is
the kind of examination and adaptation Sega v. Accolade and Sony v. Connectix hold
to be fair. None of that extends to either image, which is why neither is here.

