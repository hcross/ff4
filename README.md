# FF4 → Game & Watch

Porting **Final Fantasy IV** (Super Famicom, 1991) to run natively on the
**Nintendo Game & Watch** — a small handheld built around an STM32H7B0
microcontroller, nothing like the SNES it was designed to run on.

> **New here?** If reverse engineering, 65816 assembly, C, or SNES
> hardware are unfamiliar territory, start with the primer before reading
> the rest of this file:
> [`docs/primer/`](docs/primer/) — five short pages covering just enough
> SNES hardware, 65816 assembly, and reverse-engineering methodology to
> follow along, each pointing to authoritative external references for
> going deeper.

This repository is the **umbrella / launch point**: stable project
context, the routine-by-routine progress registry, and the operational
workflows. It does not itself contain game code — that lives in two git
submodules, below.

## Why this is possible at all, in one paragraph

The SNES's assembly code has been community-disassembled into readable,
labeled source over years of manual work. Rather than trying to run a
full software SNES emulator on a tiny microcontroller (measured: ~4-6
frames per second — nowhere near playable, see `ff4-port`'s ADR-001), this
project rewrites the game's own routines as native C, one at a time, and
**proves each rewrite behaves identically** to the original by running
both side by side and comparing their results — a technique called
*shadow execution*, explained in
[`docs/primer/03-reverse-engineering-and-shadow-execution.md`](docs/primer/03-reverse-engineering-and-shadow-execution.md).
The parts not yet rewritten simply keep running under emulation, so the
game is playable — just not yet fast — at every point along the way.

## The three repositories

| Repository | Role | What it contains |
|---|---|---|
| **[`ff4`](.)** (this repo) | Umbrella / stable context | This README, [`AGENTS.md`](AGENTS.md) (the detailed technical reference), [`DISPATCH_REGISTRY.md`](DISPATCH_REGISTRY.md) (routine-by-routine progress), [`workflows/`](workflows/) (step-by-step procedures), [`docs/primer/`](docs/primer/) (this documentation) |
| **[`ff4-gnw`](https://github.com/hcross/ff4-gnw)** | The delivery artifact | The C sources that actually compile into the Game & Watch firmware — validated routines only, nothing experimental |
| **[`ff4-port`](https://github.com/hcross/ff4-port)** | The workshop | The disassembly, the LLM-assisted translation pipeline, and the validation oracle that proves every routine before it's trusted enough to land in `ff4-gnw` |

Each of `ff4-gnw` and `ff4-port` is a standalone, independently cloneable
repository with its own README covering its specific build/tooling
details — this file stays at the "how the whole thing fits together"
level.

## How a routine actually gets ported — the full pipeline

Every routine that ends up running as native C on the device goes through
the same three-stage pipeline. Each stage is a detailed, procedural
workflow document — this section explains *why* each stage exists; the
linked documents explain exactly *how* to carry it out.

### 1. Decompile & prove per-routine equivalence — [`workflows/WF-DECOMP.md`](workflows/WF-DECOMP.md)

Starting from the disassembly, a routine is rewritten as C (by hand or
with LLM assistance — see `ff4-port`'s translation pipeline), then proven
equivalent to the original assembly via a **spike**: a small test that
runs both versions from an identical starting state and checks they
produce identical results. Passing this is what earns a routine level
**L2** on the maturity ladder (see the primer's
[worked example](docs/primer/03-reverse-engineering-and-shadow-execution.md)).
This stage happens entirely in `ff4-port`.

### 2. Validate in a real game scenario — [`workflows/WF-VALID.md`](workflows/WF-VALID.md)

An isolated spike can't see everything — a routine might read memory it
never declared, or behave differently once real gameplay state surrounds
it. This stage wires the routine into an actual saved game moment and
shadow-compares the *whole* system's memory, not just the routine's
declared inputs/outputs, pushing it to level **L3**.

### 3. Build, flash, and confirm on real hardware — [`workflows/WF-RELEASE.md`](workflows/WF-RELEASE.md)

Desktop validation establishes *correctness*; it can't establish whether
the code is *fast enough* on hardware that is much slower and has a very
different memory architecture than a development machine. This final
stage builds the firmware, flashes it to a real Game & Watch, and confirms
the routine runs without crashing and produces the expected result on a
real screen — level **L4**, the final rung.

### The mechanism underneath all three stages: dispatch

None of this would be incremental without a way to run *some* routines as
native C and the rest interpreted, side by side, in the same running game.
That's the **dispatch** mechanism: a call to a known original-game address
is intercepted and redirected to the matching C function, if one has been
written and validated; otherwise it falls through to the interpreter,
exactly as if nothing had changed. Full mechanism and its known limits:
[`AGENTS.md`](AGENTS.md) §A.2; one-paragraph definition:
[`docs/primer/00-glossary.md`](docs/primer/00-glossary.md).

## Tracking progress

[`DISPATCH_REGISTRY.md`](DISPATCH_REGISTRY.md) is the living, generated
record of every routine's current maturity level. [`BACKLOG.md`](BACKLOG.md)
tracks broader realignment work; [`REPRISE.md`](REPRISE.md) tracks
selective requalification. None of these are hand-edited directly — see
each file's own header for how it's generated/updated.

## Where to go next

- **Want the full technical picture** (exact dispatch semantics, the
  maturity ladder's precise criteria, available tooling)?
  [`AGENTS.md`](AGENTS.md).
- **Want to actually port a routine?** [`workflows/WF-DECOMP.md`](workflows/WF-DECOMP.md).
- **Want the SNES/assembly/RE background first?** [`docs/primer/`](docs/primer/).
- **Want the translation pipeline or validation oracle in detail?**
  [`ff4-port`'s own docs](https://github.com/hcross/ff4-port/tree/main/docs).
- **Want the firmware/device integration in detail?**
  [`ff4-gnw`'s own docs](https://github.com/hcross/ff4-gnw/tree/main/docs).
