# Glossary

> **New here?** Read this alongside [`01-snes-hardware-101.md`](01-snes-hardware-101.md)
> and [`02-65816-assembly-101.md`](02-65816-assembly-101.md) — those explain
> the *why* behind these terms; this page is a quick lookup once you've
> read them once. For the exact, authoritative mechanism behind the
> FF4-specific terms (dispatch, the maturity ladder), the source of truth
> is [`AGENTS.md`](../../AGENTS.md) §A.2 and §B.2 — this glossary summarizes,
> it does not redefine.

### SNES hardware terms

- **WRAM** — the SNES's 128 KB of work RAM (`$7E0000`-`$7FFFFF`). Where
  game state (player position, HP, flags, ...) lives while the game runs.
- **Bank** — the SNES CPU addresses memory as `bank:offset` (24 bits
  total: 8-bit bank, 16-bit offset). ROM, RAM, and hardware registers each
  occupy different bank ranges. See [`01-snes-hardware-101.md`](01-snes-hardware-101.md).
- **Direct Page (D) / Data Bank (DB)** — two CPU registers that change
  what a short instruction operand actually points to. Mixing them up is
  *the* single most common source of bugs in this kind of project. Fully
  explained in [`02-65816-assembly-101.md`](02-65816-assembly-101.md) §3.
- **DMA / HDMA** — Direct Memory Access: hardware-driven bulk data
  transfer (e.g. copying graphics data into video memory) that happens
  without the CPU executing a copy loop. HDMA is the same idea, but
  re-triggered once per scanline, used for per-line visual effects.
- **PPU / APU** — the SNES's graphics chip (Picture Processing Unit) and
  sound chip (Audio Processing Unit, built around a second CPU, the
  SPC700). Neither is the main 65816 CPU; both are controlled by writing
  to hardware registers.

### Project-specific terms

- **Dispatch** — this project's core mechanism: `ff4_dispatch_try()`
  intercepts a `JSR`/`JSL` call to a known original-game address and runs
  a hand-written C function instead of interpreting the original 65816
  assembly. Full definition: `AGENTS.md` §A.2.
- **Oracle** — "the thing we compare against to know if we're right."
  In this project, the oracle is the original ROM running under LakeSnes
  (the interpreter) — a routine's C translation is only trusted once it's
  shown to behave identically to what the interpreter would have done.
- **Spike** — a small, self-contained test program (`parity/src/spike__<addr>_*.c`)
  that runs one translated C routine and the original interpreted assembly
  from an identical starting state, then compares the results. This is
  the concrete implementation of "prove equivalence to the oracle." See
  [`ff4-port/docs/workflow/translation-cascade.md`](https://github.com/hcross/ff4-port/blob/main/docs/workflow/translation-cascade.md).
- **CONTRACT** — a structured comment block attached to every translated
  C function, declaring exactly which registers/RAM addresses it reads,
  writes, and which hardware side effects (MMIO/DMA) it triggers. The
  spike uses it to know what to compare.
- **Delegate** — the alternative to translating a routine to C: a thin
  wrapper that just asks the interpreter to run the original assembly at
  that address. Used for routines judged too complex or risky to
  hand-translate safely (see `ff4-port`'s ADR-003).
- **L0 → L4 (maturity ladder)** — the five levels of trust a dispatched
  routine can reach, from "present but empty" (L0) to "validated on real
  hardware" (L4). Authoritative definition and criteria: `AGENTS.md` §B.2;
  didactic walkthrough with a worked example:
  [`03-reverse-engineering-and-shadow-execution.md`](03-reverse-engineering-and-shadow-execution.md).
- **Shadow execution** — running the original game (via the interpreter)
  "in the shadow" of the new C reimplementation, frame by frame, to
  compare their internal state and catch divergences immediately rather
  than only when something visibly breaks on screen. See
  [`03-reverse-engineering-and-shadow-execution.md`](03-reverse-engineering-and-shadow-execution.md).
