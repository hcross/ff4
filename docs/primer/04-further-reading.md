# Further reading

Curated external references, one line each on what to go to it for. These
are independent, authoritative community/individual resources, not
maintained by this project — if a link goes stale, search the title, these
are well-known references in the SNES homebrew/reverse-engineering scene.

## 65816 CPU & assembly

- **["Assembly for the SNES" by Ersanio](https://ersanio.gitbook.io/assembly-for-the-snes)**
  — the most approachable complete reference for the 65816 instruction
  set, addressing modes, and idioms, written for people who've never done
  assembly before. Start here if [`02-65816-assembly-101.md`](02-65816-assembly-101.md)
  left you wanting the full picture.
- **[65816 opcode & cycle reference (superfamicom wiki)](https://wiki.superfamicom.org/65816-reference)**
  — the precise, authoritative table of every opcode, its addressing
  modes, byte length, and cycle cost. What you reach for when you need an
  exact answer, not an explanation.

## SNES hardware (PPU / APU / DMA)

- **[SNESdev wiki](https://snes.nesdev.org/wiki)** — community-maintained,
  register-by-register hardware reference. Good starting point for "what
  does this specific register do."
- **[Fullsnes by Martin Korth](https://problemkaputt.de/fullsnes.htm)** —
  an extremely dense, extremely complete reference covering the CPU, PPU,
  SPC700/DSP audio chip, DMA/HDMA, and the many documented hardware edge
  cases and "unpredictable things" real SNES games had to work around.
  The reference of last resort when something behaves unexpectedly.

## Reverse-engineering methodology (the projects this one learns from)

- **[zelda3](https://github.com/snesrev/zelda3)** — a complete, playable
  C reimplementation of *The Legend of Zelda: A Link to the Past*, built
  with the exact same "run the original ROM under emulation, shadow-compare
  every frame" methodology this project follows (see
  [`03-reverse-engineering-and-shadow-execution.md`](03-reverse-engineering-and-shadow-execution.md)).
  Reading its `zelda_cpu_infra.c` (the validation harness) and
  `variables.h` (how original RAM addresses map onto named C variables)
  is the single most directly transferable reference for how this kind of
  port is actually built.
- **[snesrev/smw](https://github.com/snesrev/smw)** (Super Mario World,
  actually a monorepo shipping three related ports) and
  **[snesrev/sm](https://github.com/snesrev/sm)** (an early-stage Super
  Metroid port, IDA/Hex-Rays-decompiler-driven rather than hand-translated
  — its own README calls it buggy) — sibling projects under the same
  [snesrev](https://github.com/snesrev) organization, using the same
  frame-by-frame dual-execution methodology on different games; useful for
  seeing how the pattern adapts to a different game's specifics.
- **[snes2asm](https://github.com/nathancassano/snes2asm)** — a
  disassembly-tooling project that turns a SNES ROM into an editable,
  reassemblable project. Not used directly by this project (which starts
  from an existing hand-annotated disassembly), but a good reference for
  how automated code/data separation and hardware-register annotation
  work on 65816 ROMs in general.

## This project's own reference material

- [`AGENTS.md`](../../AGENTS.md) — the authoritative, stable context for
  this project's own architecture and vocabulary (the dispatch mechanism,
  the maturity ladder, the three-repository layout).
- [`../../workflows/`](../../workflows/) — the step-by-step procedures
  (WF-DECOMP, WF-VALID, WF-RELEASE) that put this primer's concepts into
  practice.
