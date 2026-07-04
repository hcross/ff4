# SNES hardware, in twenty minutes

> You don't need to memorize any of this to follow the rest of the
> documentation — treat it as a map you can come back to. If a term here
> is unfamiliar later, this is where to look it up; the
> [glossary](00-glossary.md) has the one-line version.

## Why this matters for a *porting* project

This project isn't writing a new game — it's taking Final Fantasy IV,
originally written for a specific 1990 game console, and making the exact
same game logic run on a completely different, much smaller piece of
hardware (a Nintendo Game & Watch handheld). To do that safely, you have
to understand what the original hardware actually did, because the game's
assembly code is full of instructions that only make sense in terms of
*that* hardware — "write this byte to this address" only tells you
something once you know whether that address is memory, or a command to a
graphics chip.

## The big picture: one CPU, several helpers

The SNES (Super Nintendo Entertainment System / Super Famicom) is built
around one main processor, the **65816** (a 16-bit evolution of the
6502 CPU used in the original NES and the Apple II — see
[`02-65816-assembly-101.md`](02-65816-assembly-101.md) for the CPU itself),
plus several dedicated chips it talks to by writing to fixed memory
addresses:

- The **PPU** (Picture Processing Unit) draws the screen: background
  layers, sprites, and a handful of special hardware effects (like
  "Mode 7," a trick used for rotated/scaled backgrounds — famously the
  SNES's signature visual effect).
- The **APU** (Audio Processing Unit) is, surprisingly, an entire *second*
  computer: a Sony SPC700 CPU with its own small RAM, dedicated to sound.
  The main CPU doesn't generate sound directly — it sends short messages
  to the APU (a "mailbox" handshake) and the APU's own program does the
  rest.
- The **DMA/HDMA controller** moves blocks of data (typically from ROM or
  RAM into the PPU's video memory) without the main CPU spending time
  copying byte by byte. HDMA does the same thing but re-triggers once per
  scanline, which is how the SNES pulls off effects like a background
  that scrolls differently line by line.

None of these chips share one flat memory space with the CPU the way a
modern computer's RAM does — the CPU *writes to registers* (specific fixed
addresses) to tell the PPU/APU/DMA controller what to do, and reads other
registers to get results back. Recognizing "this instruction is talking to
hardware, not just moving data around" is a recurring, important skill
throughout this project — see Pitfall 13 in
[`ff4-port/prompts/pitfalls.yaml`](https://github.com/hcross/ff4-port/blob/main/prompts/pitfalls.yaml)
for exactly the kind of bug that happens when this distinction is missed.

## Memory map, at a glance

The CPU addresses memory as a 24-bit `bank:offset` pair. The parts that
matter most for this project:

| Address range | What's there |
|---|---|
| `$7E0000`-`$7FFFFF` | **WRAM** — 128 KB of work RAM, where all game state lives (player stats, map position, flags, ...) |
| `$2100`-`$21FF`, `$4200`-`$43FF` | **Hardware registers** — PPU, APU mailbox, DMA/HDMA controllers. Writing here does something physical, it does not just store a value. |
| `$008000`+ (in this game's mapping) | **ROM** — the game's code and data, read-only |

The first 8 KB of WRAM (`$7E0000`-`$7E1FFF`) is also *mirrored* into the
low part of several other banks, which is a common source of "wait, isn't
that two different addresses?" confusion when reading disassembled code —
see [`02-65816-assembly-101.md`](02-65816-assembly-101.md) §1 for the
precise rule.

## Why this project needs an emulator at all

Every one of the above chips has its own timing quirks, edge cases, and
occasionally undocumented behavior (real, shipped SNES games sometimes
rely on hardware quirks that aren't obvious from a register's stated
purpose). Rather than re-deriving all of that from scratch, this project
reuses [LakeSnes](https://github.com/elzo-d/LakeSnes), an existing,
well-tested software SNES emulator, both as the **reference** for "what is
the original game actually supposed to do here" and, for anything not yet
reimplemented, as the **execution engine** itself. See
[`03-reverse-engineering-and-shadow-execution.md`](03-reverse-engineering-and-shadow-execution.md)
for how that reference is used to validate the port as it's built.

## Going deeper

This page deliberately stops at "enough to follow the rest of the docs."
For the full, precise register-level reference:

- [SNESdev wiki](https://snes.nesdev.org/wiki) — the community-maintained
  hardware reference, register by register.
- [Fullsnes](https://problemkaputt.de/fullsnes.htm) by Martin Korth — an
  extremely dense, extremely complete reference covering the CPU, PPU,
  APU/SPC700, DMA/HDMA edge cases, and the many "unpredictable things"
  real games had to work around.

See also [`04-further-reading.md`](04-further-reading.md) for the full
curated list, including 65816-assembly-specific references.
